# Project State

_Generated: 2026-06-17_

---

## MVP Completion: 65%

The entire architecture is designed and written. The core is real code, not
scaffolding. But several things prevent it from running end-to-end without
additional work. The 35% gap is specific, fixable, and documented below.

---

## 1. Implemented

### Backend

| Area | Status | Files |
|---|---|---|
| All 11 SQLAlchemy models | Done | `app/models/*.py` |
| Alembic migration (001_initial_schema) | Done | `migrations/versions/001_initial_schema.py` |
| JWT auth with bcrypt + refresh token rotation | Done | `services/auth_service.py`, `routers/auth.py` |
| Patient CRUD (scoped per doctor) | Done | `routers/patients.py` |
| Consultation lifecycle endpoints | Done | `routers/consultations.py` |
| R2 presigned upload URL generation | Done | `services/audio_service.py` |
| Sarvam AI transcription + Whisper fallback | Done | `services/transcription_service.py` |
| Claude structured SOAP generation (temperature=0) | Done | `services/note_service.py` |
| AI safety prompt (v1) | Done | `app/prompts/v1/soap_generation.txt` |
| Prompt versioning (stored on every generated note) | Done | `models/prompt_version.py` |
| BackgroundTask pipeline (transcribe → generate) | Done | `tasks/process_consultation.py` |
| Note approval + immutable locking | Done | `routers/consultations.py` → `PUT /approve` |
| Edit tracking (fields_edited, edit_time_seconds) | Done | `models/approved_note.py` |
| WeasyPrint PDF generation | Done | `services/pdf_service.py` |
| Free quota enforcement (10 consultations/month) | Done | `routers/consultations.py` → `POST /consultations` |
| Dockerfile + docker-compose | Done | Root level |

### Frontend

| Area | Status | Files |
|---|---|---|
| Login + Register pages | Done | `app/(auth)/login`, `app/(auth)/register` |
| JWT storage + auto-refresh on 401 | Done | `lib/auth.ts`, `lib/api.ts` |
| Dashboard layout with auth guard | Done | `app/(dashboard)/layout.tsx` |
| Dashboard (recent consultations list) | Done | `app/(dashboard)/dashboard/page.tsx` |
| New Consultation flow (form → record → process) | Done | `app/(dashboard)/consultations/new/page.tsx` |
| AudioRecorder (MediaRecorder API + file upload fallback) | Done | `components/consultation/AudioRecorder.tsx` |
| ProcessingScreen (2s polling with step indicators) | Done | `components/consultation/ProcessingScreen.tsx` |
| Consultation detail (SOAPEditor + ApprovedNote view) | Done | `app/(dashboard)/consultations/[id]/page.tsx` |
| SOAPEditor (editable fields + approve/regenerate) | Done | `components/consultation/SOAPEditor.tsx` |
| PDF download (fetch with auth header) | Done | `consultations/[id]/page.tsx` → `handleDownloadPdf` |
| Patients page (list + inline add) | Done | `app/(dashboard)/patients/page.tsx` |
| Settings page (profile + subscription info) | Done | `app/(dashboard)/settings/page.tsx` |
| Typed API client | Done | `lib/api.ts` |
| Shared TypeScript types | Done | `lib/types.ts` |

---

## 2. Partially Implemented

### Critical partial: BackgroundTask DB session (will fail under load)

`process_consultation_pipeline` receives the request's `db: Session` from the
FastAPI router. FastAPI guarantees background tasks run before dependency cleanup,
so it works in development. Under concurrent load, the same session used by the
request handler is reused by the background task — this causes `DetachedInstanceError`
or stale reads when multiple requests share the pool.

**Fix required in `tasks/process_consultation.py`:**
```python
# Current (fragile)
def process_consultation_pipeline(consultation_id: uuid.UUID, db: Session) -> None:
    ...

# Fix: own session, not the request's
from app.database import SessionLocal

def process_consultation_pipeline(consultation_id: uuid.UUID) -> None:
    db = SessionLocal()
    try:
        ...
    finally:
        db.close()
```

And in `routers/consultations.py` → `process_consultation`:
```python
# Remove db from the background task call
background_tasks.add_task(process_consultation_pipeline, consultation_id)
```

Same fix needed in `regenerate_note`.

### Quota reset never runs

`doctor.consultations_this_month` increments correctly but nothing resets it to 0
at the start of each calendar month. Free-tier doctors will hit their cap permanently
after 10 consultations.

**Fix required:** A monthly cron endpoint or a reset check on login/consultation
creation that compares the current month against the last reset date.

### Regeneration re-transcribes unnecessarily

When a doctor clicks "Regenerate Note", the pipeline re-downloads the audio and
re-transcribes it before generating a new note. The existing transcript is deleted
and replaced. This wastes time (~10–15 seconds) and Sarvam API credits.

**Fix:** In the regenerate route, check if a transcript already exists. If yes,
skip transcription and start the pipeline at the generation step.

### Audit logging exists in schema, not in code

The `audit_logs` table and model are complete. No router currently writes to it.
All audit-worthy events (login, note approved, pdf exported) are silently missing
from the audit trail.

### Usage metrics table never written

`usage_metrics` table exists and has the right schema. Nothing writes to it after
consultations or approvals.

### WhatsApp share link is broken by design

The WhatsApp share button opens `wa.me/?text=<pdf_url>` where `pdf_url` is the
backend `/pdf` endpoint. That endpoint requires `Authorization: Bearer <token>`.
Anyone who receives the WhatsApp link cannot open the PDF — they'd get a 401.

**Fix options:**
1. Generate a time-limited public URL from R2 (presigned GET, 24hr expiry) after
   approval and share that URL instead.
2. For MVP: share the note text directly (not a PDF link) via WhatsApp.

### shadcn/ui component files not generated

`package.json` includes all `@radix-ui/*` dependencies and `components/ui/` directory
exists but is empty. Pages work because they use inline Tailwind directly, but
`shadcn/ui` is not initialised (`components.json` missing, no `cn()` usage with
shadcn components). This is not a blocker — the UI works — but the dependency is
declared without being used.

---

## 3. Missing

### Will block running locally

| Missing | Impact |
|---|---|
| `backend/.env` with real API keys | Backend won't start, all AI calls will fail |
| `frontend/.env.local` | Frontend won't know where the backend is |
| `npm install` not run | `node_modules` doesn't exist |
| `pip install -r requirements.txt` not run | Python deps not installed |
| `alembic upgrade head` not run | Zero tables in the database |
| R2 bucket + CORS configuration | Audio uploads from browser will fail with CORS error |

### Will block going to paid users

| Missing | Impact |
|---|---|
| Razorpay payment integration | No way for a doctor to upgrade to Pro. Settings page has a "Contact to Upgrade" WhatsApp link as a placeholder. |
| Monthly quota reset logic | Free-tier doctors permanently blocked after 10 consultations |
| Sentry not initialised | `sentry-sdk` in requirements.txt but `sentry_sdk.init()` never called in `main.py` |
| PostHog not initialised | In `package.json` but never called in frontend |
| Rate limiting on auth endpoints | `/auth/login` has no brute-force protection |

### Missing pages / flows

| Missing | Notes |
|---|---|
| Full consultation history page (`/consultations`) | Dashboard shows last 10 only. No paginated history view. |
| Consultation search/filter | No way to find a specific patient's past visits |
| Email verification flow | `users.is_verified` column exists, no email sending or verification link |
| Password reset / forgot password | Not implemented at all |
| Doctor onboarding checklist | First-time user sees an empty dashboard with no guidance |

---

## 4. Current Architecture

```
Browser (Next.js / Vercel)
    │  JWT in localStorage, auto-refresh on 401
    │  MediaRecorder API → direct PUT to R2 (presigned URL)
    │  2-second polling for status during processing
    ▼
FastAPI (Railway :8000)
    │  /api/v1/auth, /patients, /consultations
    │  JWT HS256 verification on every request
    │  BackgroundTasks (sync, not Celery)
    ├──▶ PostgreSQL 15 (Railway) — 11 tables
    ├──▶ Cloudflare R2 — audio files + PDFs
    ├──▶ Sarvam AI saarika:v2 — Hinglish transcription
    ├──▶ OpenAI Whisper — fallback transcription
    └──▶ Anthropic claude-sonnet-4-6 — SOAP generation
              temperature=0, forced tool_use, structured output
```

**Data flow for a consultation:**
```
Doctor records → R2 (presigned PUT) → POST /process → BackgroundTask:
    status: uploading → transcribing → transcribed → generating → generated
Frontend polls /status every 2s → detects "generated" → loads note
Doctor edits in SOAPEditor → PUT /approve → ApprovedNote (immutable)
GET /pdf → WeasyPrint → PDF bytes streamed back
```

---

## 5. Current Blockers

### Blocker 1 — BackgroundTask DB session bug (data integrity risk)
**File:** `backend/app/tasks/process_consultation.py`
**Severity:** High — will cause intermittent `DetachedInstanceError` under any load
**Fix time:** 30 minutes

### Blocker 2 — External service credentials not configured
No API keys = nothing works. R2 CORS not configured = audio uploads fail silently.
**Fix time:** 1–2 hours (account setup + key generation + CORS policy on R2)

### Blocker 3 — Dependencies not installed
`npm install` and `pip install` not run. Zero runnable state.
**Fix time:** 10 minutes

### Blocker 4 — Database not migrated
`alembic upgrade head` not run. All API calls will fail with "relation does not exist".
**Fix time:** 5 minutes (after credentials configured)

### Blocker 5 — WhatsApp share broken
Sharing the authenticated PDF URL over WhatsApp doesn't work without a public R2 URL.
**Fix time:** 2 hours (generate presigned R2 GET URL on approval, store it)

---

## 6. Next Recommended Milestone

**Goal:** Complete end-to-end flow with one real Hinglish consultation. Everything
else is blocked on this working first.

### Step 1 — Fix the DB session bug (30 min)
Refactor `process_consultation_pipeline` to create its own `SessionLocal()` session.
Update both `process_consultation` and `regenerate_note` routes to not pass `db`.

### Step 2 — Configure external services (1–2 hrs)
- Create Cloudflare R2 bucket, set CORS policy (allow PUT from localhost:3000)
- Get Anthropic API key
- Get Sarvam AI API key (or OpenAI key for Whisper-only mode)
- Fill `backend/.env` and `frontend/.env.local`

### Step 3 — Run locally (15 min)
```bash
docker-compose up db redis -d
cd backend && pip install -r requirements.txt && alembic upgrade head
uvicorn app.main:app --reload --port 8000

cd frontend && npm install && npm run dev
```

### Step 4 — Test the full flow
1. Register as a doctor
2. Create a new consultation (patient: "Ramesh Kumar, 45M")
3. Record 30 seconds of Hinglish audio: _"Haan, toh aapko ghutne mein dard hai..."_
4. Verify transcript is generated correctly
5. Verify SOAP note has no hallucinated content
6. Edit one field, approve
7. Download PDF — verify it renders correctly

### Step 5 — Fix WhatsApp share (2 hrs)
Store a time-limited presigned R2 URL on `ApprovedNote.pdf_storage_key` at approval
time. Use that URL in the WhatsApp share instead of the authenticated backend endpoint.

### Step 6 — Add Sentry + PostHog initialisation (1 hr)
Both SDKs are installed but not initialised. Add `sentry_sdk.init()` in `main.py`
and `posthog.init()` in `layout.tsx`. Needed to detect failures during beta.

**After these 6 steps: fully runnable MVP, ready for the first beta doctor.**

---

## 7. Known Bugs

| Bug | Location | Severity |
|---|---|---|
| BackgroundTask receives request-scoped `db` session | `tasks/process_consultation.py` | High |
| Regeneration always re-transcribes (wastes Sarvam credits) | `tasks/process_consultation.py` | Medium |
| WhatsApp share URL requires auth header — recipients get 401 | `consultations/[id]/page.tsx` | Medium |
| Monthly quota counter never resets | `routers/consultations.py` | Medium |
| Audit log writes not connected to any router | All routers | Low (table exists, just unused) |
| Usage metrics never written | `tasks/process_consultation.py` | Low |
| `components/ui/` empty — shadcn not initialised | `frontend/components/ui/` | Low (UI works without it) |
| No rate limiting on `POST /auth/login` | `routers/auth.py` | Low (for 10 doctors) |
