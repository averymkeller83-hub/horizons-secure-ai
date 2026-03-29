-- Horizons Secure AI — PostgreSQL Schema
-- Phase 1: Foundation tables for customers, leads, repairs, and conversations

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- CUSTOMERS
-- ============================================================
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    address TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_customers_email ON customers (email);
CREATE INDEX idx_customers_phone ON customers (phone);
CREATE INDEX idx_customers_created_at ON customers (created_at);

-- ============================================================
-- LEADS
-- ============================================================
CREATE TYPE lead_status AS ENUM (
    'new',
    'contacted',
    'qualified',
    'converted',
    'lost'
);

CREATE TYPE lead_source AS ENUM (
    'web_inquiry',
    'social_media',
    'classifieds',
    'referral',
    'walk_in',
    'other'
);

CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    source lead_source NOT NULL DEFAULT 'other',
    status lead_status NOT NULL DEFAULT 'new',
    score SMALLINT CHECK (score >= 0 AND score <= 100),
    device_description TEXT,
    issue_summary TEXT,
    contact_info JSONB,
    outreach_history JSONB DEFAULT '[]'::jsonb,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_leads_status ON leads (status);
CREATE INDEX idx_leads_score ON leads (score DESC);
CREATE INDEX idx_leads_customer_id ON leads (customer_id);
CREATE INDEX idx_leads_created_at ON leads (created_at);

-- ============================================================
-- REPAIRS
-- ============================================================
CREATE TYPE repair_status AS ENUM (
    'intake',
    'diagnosed',
    'awaiting_parts',
    'in_progress',
    'testing',
    'completed',
    'picked_up',
    'cancelled'
);

CREATE TYPE device_type AS ENUM (
    'phone',
    'tablet',
    'laptop',
    'desktop',
    'console',
    'tv',
    'audio',
    'other'
);

CREATE TABLE repairs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    status repair_status NOT NULL DEFAULT 'intake',
    device_type device_type NOT NULL DEFAULT 'other',
    device_brand VARCHAR(100),
    device_model VARCHAR(200),
    serial_number VARCHAR(100),
    issue_description TEXT NOT NULL,
    diagnosis TEXT,
    estimated_cost NUMERIC(10, 2),
    final_cost NUMERIC(10, 2),
    estimated_completion DATE,
    technician_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_repairs_customer_id ON repairs (customer_id);
CREATE INDEX idx_repairs_status ON repairs (status);
CREATE INDEX idx_repairs_created_at ON repairs (created_at);

-- ============================================================
-- REPAIR STATUS HISTORY (event log)
-- ============================================================
CREATE TABLE repair_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repair_id UUID NOT NULL REFERENCES repairs(id) ON DELETE CASCADE,
    old_status repair_status,
    new_status repair_status NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_repair_status_history_repair_id ON repair_status_history (repair_id);

-- ============================================================
-- CONVERSATIONS
-- ============================================================
CREATE TYPE conversation_type AS ENUM (
    'intake',
    'status_inquiry',
    'lead_outreach',
    'general'
);

CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    repair_id UUID REFERENCES repairs(id) ON DELETE SET NULL,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    type conversation_type NOT NULL DEFAULT 'general',
    summary TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ
);

CREATE INDEX idx_conversations_customer_id ON conversations (customer_id);
CREATE INDEX idx_conversations_repair_id ON conversations (repair_id);
CREATE INDEX idx_conversations_type ON conversations (type);

-- ============================================================
-- CONVERSATION MESSAGES
-- ============================================================
CREATE TYPE message_role AS ENUM ('system', 'user', 'assistant');

CREATE TABLE conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role message_role NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER,
    model VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_conversation_messages_conversation_id ON conversation_messages (conversation_id);
CREATE INDEX idx_conversation_messages_created_at ON conversation_messages (created_at);

-- ============================================================
-- PROMPTS (versioned prompt templates)
-- ============================================================
CREATE TABLE prompts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    system_prompt TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (name, version)
);

CREATE INDEX idx_prompts_name_active ON prompts (name, is_active);

-- ============================================================
-- UPDATED_AT TRIGGER
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_repairs_updated_at
    BEFORE UPDATE ON repairs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
