-- =============================================================================
-- Setup Unity Catalog Volumes for HLS Serverless Demo
-- =============================================================================
-- Run this script to create the required volumes for the demo

-- Create functional_testing volume for test file storage
CREATE VOLUME IF NOT EXISTS maggiedatabricksterraform_dbw.synthea.functional_testing
COMMENT 'Stores test files created during functional testing job';

-- Verify volumes exist
SHOW VOLUMES IN maggiedatabricksterraform_dbw.synthea;

