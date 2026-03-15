-- Runtime compatibility migration for HIA
-- Execute this in Supabase SQL editor if your schema is older.

ALTER TABLE IF EXISTS chat_sessions
ADD COLUMN IF NOT EXISTS title TEXT;

ALTER TABLE IF EXISTS chat_messages
ADD COLUMN IF NOT EXISTS content TEXT;

CREATE TABLE IF NOT EXISTS app_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    level TEXT,
    event TEXT,
    message TEXT,
    details TEXT,
    user_id UUID NULL,
    session_id UUID NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_app_logs_created_at ON app_logs(created_at DESC);
