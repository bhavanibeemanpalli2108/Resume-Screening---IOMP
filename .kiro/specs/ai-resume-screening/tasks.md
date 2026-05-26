# Implementation Tasks: AI-Powered Resume Screening and Shortlisting System

- [x] 1. Set up config.py and core/preprocessing.py
  - [x] 1.1 Implement config.py with all env vars and ATS weight constants
  - [x] 1.2 Implement core/preprocessing.py with clean_text(), normalize_resume(), normalize_job_description()

- [x] 2. Update core/scoring.py to 4-component ATS formula
  - [x] 2.1 Update final_score() to use 0.40 semantic + 0.30 skill + 0.20 project + 0.10 experience weights

- [x] 3. Implement services/resume_service.py
  - [x] 3.1 Implement extract_projects() with hybrid rule-based + Ollama fallback
  - [x] 3.2 Implement score_projects() using embedding cosine similarity
  - [x] 3.3 Implement process_resume() orchestrating the full pipeline

- [x] 4. Implement services/job_service.py
  - [x] 4.1 Implement create_job() with normalization, embedding, and skill extraction
  - [x] 4.2 Implement get_active_jobs() and get_recruiter_jobs()

- [x] 5. Implement services/matching_service.py
  - [x] 5.1 Implement semantic_score(), skill_score(), experience_score() sub-scorers
  - [x] 5.2 Implement compute_match() with composite ATS formula
  - [x] 5.3 Implement build_faiss_index() and faiss_top_k()
  - [x] 5.4 Implement rank_candidates()

- [x] 6. Update database/queries.py for new schema columns
  - [x] 6.1 Update insert_resume() to include skills, experience_years, projects fields
  - [x] 6.2 Update insert_job() to include skills field
  - [x] 6.3 Update insert_application() to include score breakdown columns

- [x] 7. Update pages/3_Candidate_Dashboard.py
  - [x] 7.1 Replace inline resume processing with resume_service.process_resume()
  - [x] 7.2 Pass extracted skills and project score to compute_match() on Apply

- [x] 8. Update pages/4_Recruiter_Dashboard.py
  - [x] 8.1 Replace inline job creation with job_service.create_job()
  - [x] 8.2 Wire Shortlist button to send_shortlist_email() after status update

- [x] 9. Update database/schema.sql with final schema
  - [x] 9.1 Write complete SQL DDL for all 4 tables matching the design

- [x] 10. Write property-based and unit tests
  - [x] 10.1 tests/test_matching.py — Properties 5, 6, 7, 8, 9 + unit edge cases
  - [x] 10.2 tests/test_auth.py — Property 10 + unit login/register cases
  - [x] 10.3 tests/test_embeddings.py — Property 3
  - [x] 10.4 tests/test_email.py — Property 11
  - [x] 10.5 tests/test_job_service.py — Property 12
