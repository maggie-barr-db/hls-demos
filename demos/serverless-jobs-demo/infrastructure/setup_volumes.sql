-- =============================================================================
-- Setup Unity Catalog Volumes for HLS Serverless Demo
-- =============================================================================
-- Run this script to create the required volumes for the demo

-- Create schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS mbarrett.synthea
COMMENT 'Healthcare demo schema for Synthea data';

-- Create landing volume for raw data
CREATE VOLUME IF NOT EXISTS mbarrett.synthea.landing
COMMENT 'Stores raw Synthea healthcare data files for bronze ingestion';

-- Create admin_configs volume for requirements and config files
CREATE VOLUME IF NOT EXISTS mbarrett.synthea.admin_configs
COMMENT 'Stores requirements.txt, wheel files, and configuration files';

-- Create functional_testing volume for test file storage
CREATE VOLUME IF NOT EXISTS mbarrett.synthea.functional_testing
COMMENT 'Stores test files created during functional testing job';

-- Verify volumes exist
SHOW VOLUMES IN mbarrett.synthea;

