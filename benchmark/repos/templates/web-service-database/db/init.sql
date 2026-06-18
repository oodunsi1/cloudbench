-- Schema for the CloudBench AWS RDS API.
-- The app also creates this table on demand, so a fresh database works with no manual step.
CREATE TABLE IF NOT EXISTS items (
    id   SERIAL PRIMARY KEY,
    name TEXT NOT NULL
);
