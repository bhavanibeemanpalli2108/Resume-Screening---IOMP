-- ============================================================
-- AI Resume Screening System — Supabase Schema
-- Run in: Supabase Dashboard → SQL Editor → New Query
-- ============================================================

-- Enable pgvector extension (required for VECTOR type)
-- Uncomment if not already enabled in your Supabase project:
-- CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- Table: users
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       TEXT UNIQUE NOT NULL,
    password    TEXT NOT NULL,
    role        TEXT NOT NULL CHECK (role IN ('candidate', 'recruiter')),
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- Table: resumes
-- ============================================================
CREATE TABLE IF NOT EXISTS resumes (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    extracted_text   TEXT,
    embedding        JSONB,
    file_name        TEXT,
    file_path        TEXT,
    skills           TEXT[],
    experience_years INT,
    projects         JSONB,
    uploaded_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id)
);

-- ============================================================
-- Table: jobs
-- ============================================================
CREATE TABLE IF NOT EXISTS jobs (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recruiter_id  UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title         TEXT NOT NULL,
    description   TEXT NOT NULL,
    embedding     JSONB,
    skills        TEXT[],
    deadline      DATE NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- Table: applications
-- ============================================================
CREATE TABLE IF NOT EXISTS applications (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id            UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    similarity_score  FLOAT NOT NULL DEFAULT 0,
    semantic_score    FLOAT,
    skill_score       FLOAT,
    project_score     FLOAT,
    experience_score  FLOAT,
    status            TEXT NOT NULL DEFAULT 'applied'
                        CHECK (status IN ('applied', 'shortlisted', 'rejected')),
    applied_at        TIMESTAMPTZ DEFAULT now(),
    UNIQUE(candidate_id, job_id)
);

-- ============================================================
-- Storage bucket: resumes (Private)
-- Create manually in Supabase Dashboard → Storage → New Bucket
-- Name: resumes
-- Public: false (Private)
-- ============================================================
