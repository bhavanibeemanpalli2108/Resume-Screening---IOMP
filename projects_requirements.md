# Requirements: AI-Powered Resume Screening and Shortlisting System

## Overview

An AI-driven resume screening platform built with Streamlit and Supabase that automates candidate evaluation and shortlisting. The system provides dual-role access (candidate / recruiter), semantic resume-to-JD matching, ATS-style scoring, and automated email notifications.

---

## Glossary

| Term | Definition | Source File |
|---|---|---|
| Resume | PDF or DOCX file uploaded by a candidate | `core/parser.py` |
| Embedding | Float vector representation of text via `all-MiniLM-L6-v2` | `models/sbert_model.py`, `core/embeddings.py` |
| ATS Score | Composite match score: 40% semantic + 30% skill + 20% project + 10% experience | `core/scoring.py` |
| Skill Match | Ratio of overlapping skills between resume and JD | `core/scoring.py` |
| Shortlist | Recruiter action that marks a candidate as shortlisted and triggers email | `pages/4_Recruiter_Dashboard.py` |
| Threshold | Recruiter-defined minimum ATS score (0–100%) for shortlisting | `pages/4_Recruiter_Dashboard.py` |
| FAISS | Vector index for fast similarity search across resume embeddings | `core/similarity.py` |
| Supabase | PostgreSQL-backed BaaS used for auth, data, and file storage | `database/db.py` |

---

## Requirements

### REQ-01: User Registration

**Description:** The system shall allow any visitor to register as either a candidate or a recruiter.

**Acceptance Criteria:**
- WHEN a visitor submits a valid email, password, and role selection on the Register page, THEN the system shall hash the password using bcrypt and insert a new row into the `users` table with columns `(id, email, password, role, created_at)`.
- WHEN a visitor submits an email that already exists in the `users` table, THEN the system shall display an error message "Email already registered." and shall not insert a duplicate row.
- WHEN a visitor submits an empty email or empty password, THEN the system shall display a validation error and shall not call `register_user()`.

---

### REQ-02: User Login and Session Management

**Description:** The system shall authenticate users and route them to the correct dashboard based on role.

**Acceptance Criteria:**
- WHEN a user submits valid credentials, THEN `login_user()` shall return the user record, the system shall set `st.session_state["user_id"]`, `st.session_state["role"]`, and `st.session_state["logged_in"] = True`, and redirect to `pages/3_Candidate_Dashboard.py` for role `candidate` or `pages/4_Recruiter_Dashboard.py` for role `recruiter`.
- WHEN a user submits invalid credentials, THEN the system shall display "Invalid credentials." and shall not set session state.
- WHEN a page is loaded and `st.session_state["logged_in"]` is not `True`, THEN the page shall redirect to `pages/1_Login.py`.
- WHEN a candidate attempts to access the recruiter dashboard, THEN the system shall redirect to `pages/1_Login.py`.

---

### REQ-03: Resume Upload and Storage

**Description:** The system shall allow candidates to upload a PDF or DOCX resume, parse it, generate an embedding, and persist both the file and structured data.

**Acceptance Criteria:**
- WHEN a candidate uploads a PDF file, THEN `parse_resume()` shall call `extract_text_from_pdf()` and return the extracted text string.
- WHEN a candidate uploads a DOCX file, THEN `parse_resume()` shall call `extract_text_from_docx()` and return the extracted text string.
- WHEN a candidate uploads a file with an extension other than `.pdf` or `.docx`, THEN `parse_resume()` shall return `None` and the system shall display an error.
- WHEN extracted text is available, THEN `generate_embedding()` shall call `model.encode()` and return a list of floats.
- WHEN a resume row does not exist for `user_id`, THEN the system shall insert a new row into `resumes` with `(user_id, extracted_text, embedding, file_name, file_path)`.
- WHEN a resume row already exists for `user_id`, THEN the system shall update the existing row instead of inserting a duplicate.
- WHEN the file is stored, THEN it shall be uploaded to the Supabase private storage bucket `resumes` using path `{user_id}_{file_name}` with `upsert: true`.

---

### REQ-04: Skill Extraction

**Description:** The system shall extract technical skills from resume text using the predefined `SKILL_LIST` in `utils/constants.py`.

**Acceptance Criteria:**
- WHEN `extract_skills(text)` is called, THEN it shall return a deduplicated list of skills whose lowercase form appears in the lowercase resume text.
- WHEN a skill appears multiple times in the text, THEN it shall appear only once in the returned list.
- WHEN the resume text contains no skills from `SKILL_LIST`, THEN `extract_skills()` shall return an empty list `[]`.

---

### REQ-05: Experience Extraction

**Description:** The system shall extract years of experience from resume text.

**Acceptance Criteria:**
- WHEN `extract_years_of_experience(text)` is called and the text contains one or more patterns matching `\d+ years?`, THEN it shall return the maximum integer value found.
- WHEN no such pattern is found, THEN it shall return `None`.

---

### REQ-06: Contact Information Extraction

**Description:** The system shall extract email address and phone number from resume text.

**Acceptance Criteria:**
- WHEN `extract_email(text)` is called and a valid email pattern exists, THEN it shall return the first matched email string.
- WHEN `extract_phone(text)` is called and a valid phone pattern exists, THEN it shall return the first matched phone string.
- WHEN no match is found, THEN each function shall return `None`.

---

### REQ-07: ATS Composite Scoring

**Description:** The system shall compute a composite ATS score for each candidate-job pair.

**Acceptance Criteria:**
- WHEN `final_score(resume_embedding, job_embedding, resume_skills, job_skills)` is called with valid embeddings, THEN it shall return a float in the range `[0.0, 1.0]` computed as: `0.4 × cosine_similarity + 0.3 × skill_overlap + 0.2 × project_score + 0.1 × experience_score`.
- WHEN either embedding is `None`, THEN `final_score()` shall return `0`.
- WHEN `cosine_similarity(vec1, vec2)` is called with two non-zero vectors, THEN it shall return the dot product divided by the product of their L2 norms.
- WHEN either vector has L2 norm of `0`, THEN `cosine_similarity()` shall return `0`.
- WHEN `skill_overlap_score(resume_skills, job_skills)` is called with non-empty lists, THEN it shall return `len(intersection) / len(job_skills)`.
- WHEN either skills list is empty, THEN `skill_overlap_score()` shall return `0`.

> **Correctness Property (Invariant):** For any valid inputs, `final_score()` shall always return a value in `[0.0, 1.0]`.

---

### REQ-08: Job Posting by Recruiter

**Description:** The system shall allow recruiters to create job postings with a title, description, and deadline.

**Acceptance Criteria:**
- WHEN a recruiter submits a job with a non-empty title, non-empty description, and a deadline date strictly after today, THEN the system shall generate an embedding for the description and insert a row into `jobs` with `(recruiter_id, title, description, embedding, deadline)`.
- WHEN the title or description is empty, THEN the system shall display "Job title and description are required." and shall not insert.
- WHEN the deadline is today or in the past, THEN the system shall display "Deadline must be a future date." and shall not insert.

---

### REQ-09: Candidate Job Application

**Description:** The system shall allow candidates to apply to active job postings.

**Acceptance Criteria:**
- WHEN a candidate clicks "Apply" on a job whose deadline is in the future, THEN the system shall compute `final_score()` using the candidate's stored embedding and the job's embedding, and insert a row into `applications` with `(candidate_id, job_id, similarity_score, status="applied")`.
- WHEN a candidate has already applied to a job, THEN the system shall display "You have already applied." and shall not insert a duplicate row.
- WHEN a candidate has no uploaded resume, THEN the system shall display "Please upload resume first." and shall not insert an application.
- WHEN a job's deadline has passed, THEN the system shall not display the "Apply" button for that job.

---

### REQ-10: Recruiter Candidate Ranking

**Description:** The system shall display all applicants for each job, ordered by `similarity_score` descending.

**Acceptance Criteria:**
- WHEN a recruiter views a job's applicants, THEN the system shall query `applications` filtered by `job_id` and ordered by `similarity_score DESC`.
- WHEN applicants exist, THEN the system shall display each applicant's email, match score (rounded to 3 decimal places), and current status badge.
- WHEN no applicants exist, THEN the system shall display the total applicant count as `0`.

---

### REQ-11: Threshold-Based Shortlisting

**Description:** The system shall allow recruiters to shortlist individual candidates and trigger email notifications.

**Acceptance Criteria:**
- WHEN a recruiter clicks "Shortlist" for a candidate, THEN the system shall update the `applications` row to `status = "shortlisted"` and call `send_shortlist_email()` with the candidate's email and job title.
- WHEN a candidate is already shortlisted, THEN the "Shortlist" button shall not be displayed for that candidate.
- WHEN `send_shortlist_email()` is called, THEN it shall send an email via `smtp.gmail.com:465` using credentials from `EMAIL_ADDRESS` and `EMAIL_PASSWORD` environment variables.

---

### REQ-12: Secure Resume Access

**Description:** The system shall provide recruiters with time-limited signed URLs to view candidate resumes.

**Acceptance Criteria:**
- WHEN a recruiter views an applicant who has a stored `file_path`, THEN the system shall call `supabase.storage.from_("resumes").create_signed_url(file_path, 120)` and display the resulting URL as a "View Resume Securely" link.
- WHEN no `file_path` exists for a candidate, THEN the system shall display "Resume file not available."
- WHEN the signed URL is generated, THEN it shall expire after 120 seconds.

---

### REQ-13: Email Notification System

**Description:** The system shall send automated shortlist notification emails using environment-variable credentials.

**Acceptance Criteria:**
- WHEN `send_shortlist_email(to_email, job_title)` is called, THEN it shall construct a `MIMEText` message with subject "You Have Been Shortlisted", addressed from `EMAIL_ADDRESS` to `to_email`.
- WHEN the email is sent, THEN the body shall include the job title and a message from "Recruitment Team".
- WHEN `EMAIL_ADDRESS` or `EMAIL_PASSWORD` environment variables are not set, THEN the function shall raise an exception and the system shall display an error to the recruiter.
- The system shall NEVER hardcode email credentials in source code.

---

### REQ-14: UI Theme and Layout

**Description:** The system shall apply role-specific visual themes consistently across all pages.

**Acceptance Criteria:**
- WHEN `apply_role_theme("candidate")` is called, THEN the primary color shall be `#2e7d32` (green) and the background shall be `#f0f7f4`.
- WHEN `apply_role_theme("recruiter")` is called, THEN the primary color shall be `#0a66c2` (blue) and the background shall be `#eef3f8`.
- WHEN any dashboard page loads, THEN `apply_role_theme()` shall be called before rendering any content.
- WHEN a candidate is shortlisted, THEN the status badge shall display with background `#2e7d32` and white text.
- WHEN a candidate has status "applied", THEN the status badge shall display with background `#fbc02d` and black text.

---

### REQ-15: Database Schema (Supabase SQL)

**Description:** The system requires four tables in Supabase: `users`, `resumes`, `jobs`, and `applications`.

Run the following SQL commands in the Supabase SQL Editor:

```sql
-- Table: users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('candidate', 'recruiter')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: resumes
CREATE TABLE IF NOT EXISTS resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    extracted_text TEXT,
    embedding JSONB,
    file_name TEXT,
    file_path TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Table: jobs
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recruiter_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    embedding JSONB,
    deadline TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: applications
CREATE TABLE IF NOT EXISTS applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    similarity_score FLOAT DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'applied' CHECK (status IN ('applied', 'shortlisted', 'rejected')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(candidate_id, job_id)
);
```

**Storage Bucket:**
In Supabase → Storage → Create a new bucket named `resumes` with **Private** access.

---

### REQ-16: Environment Configuration

**Description:** All secrets and external service credentials shall be stored in `.env` and loaded via `python-dotenv`.

**Acceptance Criteria:**
- WHEN the application starts, THEN `load_dotenv()` shall be called before any environment variable is accessed.
- The `.env` file shall contain: `SUPABASE_URL`, `SUPABASE_KEY`, `EMAIL_ADDRESS`, `EMAIL_PASSWORD`.
- WHEN any required environment variable is missing, THEN the affected module shall raise a descriptive error.
- The `.env` file shall NEVER be committed to version control.

---

### REQ-17: Correctness Properties for Property-Based Testing

The following invariants shall hold for all valid inputs and shall be validated via property-based testing:

**P1 — Score Bounds:** `final_score()` shall always return a value in `[0.0, 1.0]` for any combination of valid embeddings and skill lists.

**P2 — Skill Overlap Symmetry:** `skill_overlap_score(A, B)` may differ from `skill_overlap_score(B, A)` (not symmetric), but both shall always be in `[0.0, 1.0]`.

**P3 — Cosine Similarity Bounds:** `cosine_similarity(v1, v2)` shall always return a value in `[-1.0, 1.0]` for any non-zero vectors.

**P4 — Parser Round-Trip:** For any PDF or DOCX file, `parse_resume(file)` shall return a non-empty string when the file contains at least one word.

**P5 — Duplicate Application Prevention:** For any `(candidate_id, job_id)` pair, the `applications` table shall contain at most one row (enforced by `UNIQUE` constraint).

**P6 — Embedding Determinism:** Calling `generate_embedding(text)` twice with the same text shall return identical float lists.
