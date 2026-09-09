-- Allow one active artifact per URL while preserving inactive history.
-- Target schema: CIROH_AIBot (Azure and the aligned local database).
-- This migration is transactional: any validation/index failure restores the
-- original UNIQUE(url) constraint automatically.

BEGIN;

LOCK TABLE "CIROH_AIBot".tblartifacts IN SHARE ROW EXCLUSIVE MODE;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM "CIROH_AIBot".tblartifacts
        WHERE isactive = TRUE
        GROUP BY url
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION
            'Cannot create active-URL uniqueness: duplicate active URLs exist';
    END IF;
END
$$;

ALTER TABLE "CIROH_AIBot".tblartifacts
    DROP CONSTRAINT IF EXISTS tblartifacts_url_key;

CREATE UNIQUE INDEX IF NOT EXISTS idx_artifact_url_active
    ON "CIROH_AIBot".tblartifacts (url)
    WHERE isactive = TRUE;

COMMIT;

-- Expected postcondition:
--   no UNIQUE(url) table constraint
--   idx_artifact_url_active UNIQUE (url) WHERE isactive = TRUE
