# Technical Architecture — Clinical Documentation Assistant

## Architecture Philosophy

This is a **monolith-first** architecture. For 10–100 doctors producing ~50–200
consultations/day, a well-structured monolith is faster to build, easier to operate,
and gives us real load data before we decompose anything.

No microservices. No distributed tracing. One deployment unit.

---

## Stack Decisions

| Layer | Choice | Why |
|---|---|---|
| **Frontend** | Next.js 14 (App Router) + TypeScript | SSR for future SEO, App Router for layouts |
| **Styling** | TailwindCSS + shadcn/ui primitives | Fast, accessible, no custom CSS debt |
| **Forms** | React Hook Form + Zod | Type-safe validation end-to-end |
| **Backend** | FastAPI (Python 3.11) | Async, auto-docs, best AI library support |
| **ORM** | SQLAlchemy 2.0 + Alembic | Mapped columns, typed queries, versioned migrations |
| **Database** | PostgreSQL 15 | JSONB for flexible fields (missing_info, fields_edited) |
| **Job queue** | FastAPI BackgroundTasks | Sufficient for <200 daily jobs. Migrate to Celery at scale. |
| **Storage** | Cloudflare R2 | S3-compatible, cheaper than AWS, Indian PoP available |
| **Transcription** | Sarvam AI `saarika:v2` → Whisper fallback | Better Hinglish + medical vocabulary than vanilla Whisper |
| **Note generation** | Claude `claude-sonnet-4-6` | Best structured output + instruction-following at temperature=0 |
| **PDF** | WeasyPrint (server-side) | No external service, full HTML/CSS control |
| **Auth** | JWT (python-jose) + bcrypt (passlib) | No external auth dependency for MVP |
| **Payments** | Razorpay | UPI support — non-negotiable for Indian market |
| **Deployment** | Railway (backend + DB + Redis) + Vercel (frontend) | Zero-ops for MVP |
| **Monitoring** | Sentry (errors) + PostHog (product analytics) | Both have generous free tiers |

**Decisions rejected and why:**

| Rejected | Why |
|---|---|
| Celery + Redis | Overkill for <200 daily jobs. Adds ops burden with no benefit at MVP scale. |
| Clerk (auth) | External dependency, cost, friction. JWT + bcrypt is sufficient for 10 doctors. |
| AWS S3 | Cloudflare R2 is cheaper, has no egress fees, Indian PoP. |
| GPT-4o | Claude outperforms on structured output adherence and medical instruction-following. |
| Vanilla Whisper | Sarvam AI `saarika:v2` is trained on Indic languages + medical vocabulary. |
| Stripe | No UPI support. Indian doctors expect UPI as default payment method. |
| Microservices | Premature complexity. Revisit after 1,000 daily consultations. |

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     CLIENT (Vercel)                           │
│                                                               │
│  Next.js 14 App Router                                        │
│  ┌───────────┐ ┌──────────────┐ ┌────────────┐ ┌─────────┐  │
│  │  /login   │ │ /consultations│ │/consultations│ │/patients│  │
│  │ /register │ │    /new      │ │   /[id]    │ │/settings│  │
│  └───────────┘ └──────────────┘ └────────────┘ └─────────┘  │
│                                                               │
│  Key components:                                              │
│  AudioRecorder — MediaRecorder API + R2 direct upload        │
│  ProcessingScreen — polls /status every 2s                   │
│  SOAPEditor — editable fields, edit-time tracking            │
└─────────────────────────┬────────────────────────────────────┘
                          │ HTTPS REST  (Bearer JWT)
┌─────────────────────────▼────────────────────────────────────┐
│                   API SERVER (Railway)                        │
│                                                               │
│  FastAPI — /api/v1/*                                          │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Routers                                              │    │
│  │  /auth   — register, login, refresh, logout, me      │    │
│  │  /patients — CRUD (scoped to doctor)                  │    │
│  │  /consultations — create, upload-url, process,        │    │
│  │                   status, approve, pdf, regenerate    │    │
│  └──────────────────────┬───────────────────────────────┘    │
│                         │                                     │
│  ┌──────────────────────▼───────────────────────────────┐    │
│  │  Services                                             │    │
│  │  auth_service     — JWT + bcrypt + refresh rotation   │    │
│  │  audio_service    — R2 presigned URLs, upload         │    │
│  │  transcription_service — Sarvam AI → Whisper fallback │    │
│  │  note_service     — Claude structured tool use        │    │
│  │  pdf_service      — WeasyPrint HTML→PDF               │    │
│  └──────────────────────┬───────────────────────────────┘    │
│                         │                                     │
│  ┌──────────────────────▼───────────────────────────────┐    │
│  │  BackgroundTask: process_consultation_pipeline        │    │
│  │  Upload → Transcribe → Generate → Store               │    │
│  └──────────────────────────────────────────────────────┘    │
└────────────┬──────────────────┬──────────────────────────────┘
             │                  │
    ┌────────▼────┐    ┌────────▼────┐    ┌─────────────┐
    │ PostgreSQL  │    │ Cloudflare  │    │   Sarvam AI │
    │  (Railway)  │    │     R2      │    │  + Claude   │
    │             │    │  (audio,    │    │  (Anthropic)│
    │  11 tables  │    │   PDFs)     │    └─────────────┘
    └─────────────┘    └─────────────┘
```

---

## AI Pipeline

```
Doctor stops recording
        │
        ▼
Frontend uploads audio blob → R2 (presigned PUT URL, direct browser→R2)
        │
        ▼
POST /consultations/{id}/process  → triggers BackgroundTask
        │
        ▼
┌───────────────────────────────────────────────────┐
│  process_consultation_pipeline (BackgroundTask)   │
│                                                   │
│  1. status = "transcribing"                       │
│     ↓                                             │
│     audio_bytes = R2.get_object(storage_key)      │
│     ↓                                             │
│     result = sarvam.transcribe(audio_bytes)       │
│       └─ on failure → whisper.transcribe(...)     │
│     ↓                                             │
│     Transcript row saved                          │
│     status = "transcribed"                        │
│                                                   │
│  2. status = "generating"                         │
│     ↓                                             │
│     claude.messages.create(                       │
│       model="claude-sonnet-4-6",                  │
│       temperature=0,                              │
│       tools=[SOAP_TOOL],                          │
│       tool_choice={"type":"tool",                 │
│                    "name":"generate_soap_note"}   │
│     )                                             │
│     ↓                                             │
│     GeneratedNote row saved                       │
│     (prompt_version_id, model, tokens, time)      │
│     status = "generated"                          │
└───────────────────────────────────────────────────┘
        │
        ▼
Frontend poll detects status="generated"
        │
        ▼
SOAPEditor displayed → Doctor reviews/edits → Approves
        │
        ▼
ApprovedNote row saved (immutable)
fields_edited[], edit_time_seconds tracked
        │
        ▼
GET /consultations/{id}/pdf → WeasyPrint → PDF bytes returned
```

**AI Safety — enforced in system prompt and tool schema:**
- Temperature = 0 (no creativity)
- Tool use forced (`tool_choice: {type: "tool"}`) — no free-text response possible
- Every field has the instruction: "Write 'Not documented.' if absent"
- System prompt explicitly forbids inference, assumption, and gap-filling

---

## Database Schema

**11 tables. Consultation is the core entity.**

```
users (1) ────── (1) doctors (1) ────── (n) patients
                       │
                       └────── (n) consultations
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                   │
               audio_files        transcripts       generated_notes (n)
                                                          │
                                                    approved_notes (1)

+ prompt_versions  (referenced by generated_notes)
+ audit_logs       (append-only, references users)
+ refresh_tokens   (references users, for JWT revocation)
+ usage_metrics    (doctor_id + date, aggregated daily)
```

**Key design decisions:**

- `approved_notes` is a separate table from `generated_notes` — approved content is
  immutable. Re-approving replaces the approved row but never mutates the generated row.
- `generated_notes` has `prompt_version_id` — every note is traceable to the exact
  prompt that produced it.
- `consultation.patient_name` is denormalized — patient records can be deleted but
  consultation history must remain intact.
- `audit_logs` is append-only. Never updated or deleted.
- `refresh_tokens` stores `token_hash` (SHA-256), never the raw token.
- JSONB columns: `missing_information` (array of missing field names),
  `fields_edited` (which SOAP fields the doctor changed), `raw_response` (full AI
  response for debugging).

---

## API Endpoints

```
POST   /api/v1/auth/register          → { access_token, refresh_token }
POST   /api/v1/auth/login             → { access_token, refresh_token }
POST   /api/v1/auth/refresh           → { access_token, refresh_token }
POST   /api/v1/auth/logout            → 204
GET    /api/v1/auth/me                → { user, doctor }

GET    /api/v1/patients               → Patient[]  (with ?q= search)
POST   /api/v1/patients               → Patient
GET    /api/v1/patients/{id}          → Patient
PUT    /api/v1/patients/{id}          → Patient

GET    /api/v1/consultations          → ConsultationListItem[]
POST   /api/v1/consultations          → Consultation  (quota-checked)
GET    /api/v1/consultations/{id}     → Consultation  (full, with note)
POST   /api/v1/consultations/{id}/upload-url  → { upload_url, storage_key }
POST   /api/v1/consultations/{id}/process     → triggers BackgroundTask
GET    /api/v1/consultations/{id}/status      → { status, error_message }
PUT    /api/v1/consultations/{id}/approve     → ApprovedNote
POST   /api/v1/consultations/{id}/regenerate  → triggers re-generation
GET    /api/v1/consultations/{id}/pdf         → PDF bytes (application/pdf)

GET    /api/health                    → { status: "ok" }
```

All endpoints except `/api/health` require `Authorization: Bearer <access_token>`.
All data is scoped to the authenticated doctor — doctors cannot access each other's data.

---

## Security Model

| Concern | Implementation |
|---|---|
| Authentication | JWT HS256, 60-min expiry |
| Refresh tokens | SHA-256 hashed in DB, single-use rotation |
| Password storage | bcrypt (passlib), cost factor 12 |
| Audio storage | Private R2 bucket, presigned URLs (1hr expiry) |
| Doctor isolation | Every query filters by `doctor_id` from token |
| Note immutability | `approved_notes` rows replaced, never patched |
| Audit trail | Append-only `audit_logs` table |
| Quota enforcement | Free tier: 10 consultations/month, checked at creation |
| CORS | Whitelisted to `FRONTEND_URL` only |
| Secrets | Environment variables only, never in code or logs |

**HIPAA note:** Architecture is designed with HIPAA readiness in mind (audit logs,
access controls, encrypted storage, no PHI in logs). We do not claim HIPAA compliance.
Formal compliance requires additional controls (BAAs with vendors, encryption at rest
certification, etc.) to be addressed before enterprise sales.

---

## Frontend Architecture

```
app/
  (auth)/         — login, register  (no layout wrapper)
  (dashboard)/    — all protected pages share sidebar layout
    layout.tsx    — auth guard (redirects to /login if no token)
                  — calls /auth/me to verify session
    dashboard/    — consultation list (last 10)
    consultations/
      new/        — patient form → AudioRecorder → ProcessingScreen
      [id]/       — SOAPEditor (generated) or ApprovedNote view (approved)
    patients/     — patient list + inline add form
    settings/     — profile, subscription status

lib/
  api.ts          — typed fetch wrapper, auto-refresh on 401
  auth.ts         — localStorage token management
  types.ts        — all shared TypeScript interfaces
  utils.ts        — formatDate, statusLabel, statusColor, cn()
```

**Auth flow:**
1. Token stored in `localStorage` (access + refresh)
2. Every API call includes `Authorization: Bearer <token>`
3. On 401: attempt token refresh → retry → if refresh fails, redirect to `/login`
4. Dashboard layout calls `/auth/me` on mount — if it fails, clears tokens and redirects

---

## Deployment

```
Railway project
├── PostgreSQL service     ← managed, auto-backup
├── Redis service          ← session state (future), rate limiting
└── Backend service        ← FastAPI, auto-deploy on git push
    ENV: DATABASE_URL, REDIS_URL, ANTHROPIC_API_KEY,
         SARVAM_API_KEY, R2_*, SECRET_KEY, FRONTEND_URL

Vercel project
└── Frontend service       ← Next.js, auto-deploy on git push
    ENV: NEXT_PUBLIC_API_URL
```

**Local development:**

```bash
docker-compose up db redis -d        # Postgres + Redis
cd backend && alembic upgrade head   # Run migrations
uvicorn app.main:app --reload        # Backend on :8000
cd frontend && npm run dev           # Frontend on :3000
```

---

## Scaling Path

| Stage | Doctors | Consultations/day | Change needed |
|---|---|---|---|
| **Now** | 0–10 | 0–100 | Nothing. Current stack handles it. |
| **Phase 2** | 10–100 | 100–500 | Add Redis caching for status polling |
| **Phase 3** | 100–1000 | 500–5000 | Replace BackgroundTasks with Celery workers |
| **Phase 4** | 1000+ | 5000+ | Read replicas, connection pooling (PgBouncer), CDN for PDFs |

The rule: **optimise for the current order of magnitude, not the next one.**
