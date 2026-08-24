-- LifeBase warehouse bootstrap
-- Runs once on first container start (docker-entrypoint-initdb.d)

CREATE EXTENSION IF NOT EXISTS vector;

-- Medallion-style layout promised in the README
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;
