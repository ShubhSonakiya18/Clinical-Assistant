# Project Vision — Clinical Documentation Assistant

## The Problem

Indian doctors — particularly solo practitioners and small-clinic specialists — spend
60–90 minutes every day writing clinical notes. This causes burnout, limits patient
throughput, and degrades work-life balance. The problem is most acute in:

- Tier-2 and Tier-3 cities where administrative staff is scarce
- Solo practitioners with no documentation support
- Specialties with high patient volume (orthopedics, general medicine, pediatrics)

Doctors consult in **Hinglish** — a natural mix of Hindi and English medical
terminology. No existing tool handles this. Every current solution (Nuance DAX,
Abridge, Suki, Nabla) targets US hospitals, requires English-only input, and costs
far more than an Indian solo practitioner can justify.

---

## What We Are Building

An **AI Documentation Copilot** for Indian doctors.

The product listens to a consultation, transcribes it (including Hinglish), and
generates a structured clinical note. The doctor reviews, edits if needed, approves,
and exports a PDF — all in under 3 minutes.

**The AI assists. The doctor decides. Every time.**

---

## What We Are NOT Building

- A diagnosis engine
- A treatment recommendation system
- An autonomous medical AI
- An EHR replacement
- A prescription generator
- A hospital management system

The AI never makes medical decisions. It extracts and organises what the doctor
explicitly said. Human approval is mandatory and immutable.

---

## Target Market

| Dimension | Detail |
|---|---|
| Geography | India |
| Specialization | Orthopedics (initial), expanding to general medicine, pediatrics |
| Practice type | Solo practitioners, small clinics (1–3 doctors) |
| Language | Hinglish (Hindi + English medical terminology) |
| Price sensitivity | High — pricing in INR, UPI/card via Razorpay |

**Primary persona:** Dr. Arjun Mehta — solo orthopedic surgeon, Pune. Sees 35–45
patients/day. Consults in Hinglish. Currently dictates to a compounder who types,
or writes by hand. Would pay ₹2,999/month to save 1 hour/day.

---

## Business Model

| Tier | Price | Limit |
|---|---|---|
| Free | ₹0 | 10 consultations/month |
| Pro | ₹2,999/month | Unlimited |
| Annual | ₹24,999/year | Unlimited (~₹2,083/month) |

Payments via **Razorpay** (UPI + cards). GST invoices auto-generated.

---

## Core Workflow

```
Doctor opens app
    ↓
Enter patient info (name, age, sex) — 10 seconds
    ↓
Click Record → consultation audio captured in browser
    ↓
Click Stop — audio uploaded to Cloudflare R2
    ↓
AI pipeline runs: Transcription → SOAP generation (~15–25 seconds)
    ↓
Doctor reviews clinical note (editable fields)
    ↓
Doctor edits if needed → clicks Approve
    ↓
Note locked (immutable). PDF generated.
    ↓
Download PDF or share via WhatsApp
```

**Target: under 3 minutes from recording to approved note.**

---

## AI Rules (Non-Negotiable)

The AI must never:

- Add symptoms not explicitly mentioned
- Suggest diagnoses not stated by the doctor
- Infer treatments not discussed
- Fill gaps with assumptions

If information is missing from a section, the system writes exactly: **"Not documented."**

Every generated note is traceable: prompt version, model used, generation time,
token count, acceptance status, and edit time are all stored.

---

## Phased Roadmap

### Phase 1 — AI Scribe (Current)
Audio → Transcription → SOAP Note → Doctor Approval → PDF

**Goal:** 10 paying doctors. Each saves ≥50% documentation time.

### Phase 2 — Consultation Memory
Allow doctors to recall previous visits for a patient.
Surface: "Last visit — 3 weeks ago. Complaint: knee pain. Plan: physiotherapy x4."

### Phase 3 — Patient Timeline
Longitudinal patient history across all consultations with this doctor.

### Phase 4 — Clinical Continuity Assistant
Automatically surface relevant historical context when a returning patient walks in.

### Phase 5 — Healthcare Operating System
Patient intelligence layer across clinics. Cross-clinic continuity (with consent).

**Architecture supports this future. MVP never sacrifices speed for it.**

---

## Success Metrics (Tracked from Day 1)

| Metric | Target |
|---|---|
| Transcription accuracy (Hinglish) | >90% |
| SOAP note acceptance rate (no edit) | >50% in month 1, >70% by month 3 |
| Edit-to-approve time | <3 minutes |
| End-to-end processing time | <30 seconds |
| Week-4 retention | >80% |
| Doctor NPS | >40 |
| Free → Paid conversion | >30% by day 30 |

---

## North Star

> 10 doctors paying for this within 90 days.
> Each one saves at least 1 hour of documentation work per day.
> Every product and technical decision is optimised for this goal.
