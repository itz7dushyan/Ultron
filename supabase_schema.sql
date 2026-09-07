-- ==============================================================================
-- ULTRON PERSISTENT LONG-TERM MEMORY SCHEMA (SUPABASE POSTGRESQL)
-- ==============================================================================

-- 1. Table for persistent memory & key-value configuration
CREATE TABLE IF NOT EXISTS public.ultron_memory (
    id SERIAL PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    value TEXT,
    category TEXT DEFAULT 'general',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Enable Row Level Security (RLS)
ALTER TABLE public.ultron_memory ENABLE ROW LEVEL SECURITY;

-- 3. Policy for service role and authenticated access
CREATE POLICY "Allow service role full access on ultron_memory"
    ON public.ultron_memory
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Allow anon read/write access on ultron_memory"
    ON public.ultron_memory
    FOR ALL
    TO anon
    USING (true)
    WITH CHECK (true);

-- 4. Table for audit events & action telemetry
CREATE TABLE IF NOT EXISTS public.ultron_audit_events (
    id SERIAL PRIMARY KEY,
    event_id TEXT UNIQUE,
    agent_name TEXT NOT NULL,
    action TEXT NOT NULL,
    target TEXT,
    details JSONB,
    status TEXT DEFAULT 'success',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE public.ultron_audit_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow service role full access on ultron_audit_events"
    ON public.ultron_audit_events
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Allow anon read/write access on ultron_audit_events"
    ON public.ultron_audit_events
    FOR ALL
    TO anon
    USING (true)
    WITH CHECK (true);
