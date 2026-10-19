-- Rename the original HydroShare portal tables to the application names.
-- Target schema: CIROH_AIBot (Azure and the aligned local database).
-- PostgreSQL preserves all rows, indexes, constraints, and foreign-key
-- relationships when a table is renamed. Safe to run more than once.

BEGIN;

DO $$
BEGIN
    IF to_regclass(
        '"CIROH_AIBot".tblhsresearchportaltype'
    ) IS NOT NULL AND to_regclass(
        '"CIROH_AIBot".tblhsresearchportaltypes'
    ) IS NULL THEN
        ALTER TABLE "CIROH_AIBot".tblhsresearchportaltype
            RENAME TO tblhsresearchportaltypes;
    ELSIF to_regclass(
        '"CIROH_AIBot".tblhsresearchportaltype'
    ) IS NOT NULL THEN
        RAISE EXCEPTION
            'Both old and new HydroShare portal lookup tables exist; no rename was performed';
    END IF;

    IF to_regclass(
        '"CIROH_AIBot".tblartifactshsresearchportaltypes'
    ) IS NOT NULL AND to_regclass(
        '"CIROH_AIBot".trlartifactshsresearchportaltypes'
    ) IS NULL THEN
        ALTER TABLE "CIROH_AIBot".tblartifactshsresearchportaltypes
            RENAME TO trlartifactshsresearchportaltypes;
    ELSIF to_regclass(
        '"CIROH_AIBot".tblartifactshsresearchportaltypes'
    ) IS NOT NULL THEN
        RAISE EXCEPTION
            'Both old and new HydroShare portal bridge tables exist; no rename was performed';
    END IF;
END
$$;

COMMIT;
