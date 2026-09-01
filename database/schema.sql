-- LeaseGuard AI Phase 2 schema
-- This is intended to be run manually in the Supabase SQL Editor.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS properties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    address TEXT,
    city TEXT,
    state TEXT,
    postal_code TEXT,
    country TEXT,
    property_type TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'draft')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    document_type TEXT NOT NULL,
    file_name TEXT NOT NULL,
    storage_path TEXT,
    document_status TEXT NOT NULL DEFAULT 'uploaded' CHECK (document_status IN ('uploaded', 'processing', 'ready', 'error')),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    audit_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'in_progress', 'completed', 'archived')),
    total_invoice_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    audit_id UUID NOT NULL REFERENCES audits(id) ON DELETE CASCADE,
    severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'under_review', 'resolved', 'closed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS risk_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    overall_score SMALLINT NOT NULL DEFAULT 0 CHECK (overall_score BETWEEN 0 AND 100),
    risk_level TEXT NOT NULL DEFAULT 'low' CHECK (risk_level IN ('low', 'moderate', 'high', 'critical')),
    summary TEXT,
    score_breakdown JSONB NOT NULL DEFAULT '{}'::jsonb,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS recovery_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    finding_id UUID REFERENCES findings(id) ON DELETE SET NULL,
    audit_id UUID REFERENCES audits(id) ON DELETE SET NULL,
    amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'Detected' CHECK (status IN ('Detected', 'Disputed', 'Under Review', 'Recovered', 'Rejected')),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS disputes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    recovery_record_id UUID REFERENCES recovery_records(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    summary TEXT,
    status TEXT NOT NULL DEFAULT 'Draft' CHECK (status IN ('Draft', 'Submitted', 'Under Review', 'Accepted', 'Rejected', 'Recovered')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_properties_user_id ON properties(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_property_id ON documents(property_id);
CREATE INDEX IF NOT EXISTS idx_audits_user_id ON audits(user_id);
CREATE INDEX IF NOT EXISTS idx_audits_property_id ON audits(property_id);
CREATE INDEX IF NOT EXISTS idx_findings_user_id ON findings(user_id);
CREATE INDEX IF NOT EXISTS idx_findings_audit_id ON findings(audit_id);
CREATE INDEX IF NOT EXISTS idx_risk_scores_user_id ON risk_scores(user_id);
CREATE INDEX IF NOT EXISTS idx_risk_scores_property_id ON risk_scores(property_id);
CREATE INDEX IF NOT EXISTS idx_recovery_records_user_id ON recovery_records(user_id);
CREATE INDEX IF NOT EXISTS idx_recovery_records_property_id ON recovery_records(property_id);
CREATE INDEX IF NOT EXISTS idx_disputes_user_id ON disputes(user_id);
CREATE INDEX IF NOT EXISTS idx_disputes_property_id ON disputes(property_id);

-- The app uses the anonymous key together with Supabase Auth. Enforce that a
-- signed-in user can access only rows they own, rather than relying on UI filters.
ALTER TABLE properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE audits ENABLE ROW LEVEL SECURITY;
ALTER TABLE findings ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE recovery_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE disputes ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "owner access" ON properties;
CREATE POLICY "owner access" ON properties FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "owner access" ON documents;
CREATE POLICY "owner access" ON documents FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "owner access" ON audits;
CREATE POLICY "owner access" ON audits FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "owner access" ON findings;
CREATE POLICY "owner access" ON findings FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "owner access" ON risk_scores;
CREATE POLICY "owner access" ON risk_scores FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "owner access" ON recovery_records;
CREATE POLICY "owner access" ON recovery_records FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "owner access" ON disputes;
CREATE POLICY "owner access" ON disputes FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Optional: keep the timestamps fresh on update.
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_trigger
        WHERE tgname = 'set_updated_at_properties'
    ) THEN
        CREATE TRIGGER set_updated_at_properties
        BEFORE UPDATE ON properties
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_trigger
        WHERE tgname = 'set_updated_at_documents'
    ) THEN
        CREATE TRIGGER set_updated_at_documents
        BEFORE UPDATE ON documents
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_trigger
        WHERE tgname = 'set_updated_at_audits'
    ) THEN
        CREATE TRIGGER set_updated_at_audits
        BEFORE UPDATE ON audits
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_trigger
        WHERE tgname = 'set_updated_at_findings'
    ) THEN
        CREATE TRIGGER set_updated_at_findings
        BEFORE UPDATE ON findings
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_trigger
        WHERE tgname = 'set_updated_at_recovery_records'
    ) THEN
        CREATE TRIGGER set_updated_at_recovery_records
        BEFORE UPDATE ON recovery_records
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_trigger
        WHERE tgname = 'set_updated_at_disputes'
    ) THEN
        CREATE TRIGGER set_updated_at_disputes
        BEFORE UPDATE ON disputes
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;
END $$;
