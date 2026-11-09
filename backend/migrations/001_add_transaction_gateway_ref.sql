-- NakshaAI: add gateway_ref to transactions for Stripe/payment refs (Postgres)
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS gateway_ref VARCHAR;
CREATE INDEX IF NOT EXISTS ix_transactions_gateway_ref ON transactions (gateway_ref);
-- If using SQLite locally, run equivalent manually if column missing.
