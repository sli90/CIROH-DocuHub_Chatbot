-- Add many-to-many HydroShare research-portal classifications.
-- Target schema: CIROH_AIBot (Azure and the aligned local database).
-- Safe to run more than once.

BEGIN;

CREATE TABLE IF NOT EXISTS "CIROH_AIBot".tblhsresearchportaltypes (
    idhsresearchportaltype SERIAL PRIMARY KEY,
    hsresearchportaltype TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS "CIROH_AIBot".trlartifactshsresearchportaltypes (
    idartifact INTEGER NOT NULL
        REFERENCES "CIROH_AIBot".tblartifacts(idartifact)
        ON DELETE CASCADE,
    idhsresearchportaltype INTEGER NOT NULL
        REFERENCES "CIROH_AIBot".tblhsresearchportaltypes(
            idhsresearchportaltype
        )
        ON DELETE RESTRICT,
    PRIMARY KEY (idartifact, idhsresearchportaltype)
);

CREATE INDEX IF NOT EXISTS idx_artifacts_hs_research_portal_type
    ON "CIROH_AIBot".trlartifactshsresearchportaltypes (
        idhsresearchportaltype,
        idartifact
    );

INSERT INTO "CIROH_AIBot".tblhsresearchportaltypes (
    hsresearchportaltype
)
VALUES
    ('Apps'),
    ('Datasets'),
    ('Courses'),
    ('Presentations'),
    ('Events'),
    ('Notebooks')
ON CONFLICT (hsresearchportaltype) DO NOTHING;

INSERT INTO "CIROH_AIBot".tblchunktypes (idartifacttype, typename)
VALUES
    (3, 'Abstract'),
    (3, 'Spatial Coverage'),
    (3, 'Temporal Coverage'),
    (3, 'Variable Metadata'),
    (3, 'Data Services Info'),
    (3, 'File Description'),
    (3, 'Collection Contents'),
    (3, 'Subject Keywords'),
    (3, 'Related Resources Context'),
    (3, 'Citation'),
    (3, 'Creator'),
    (3, 'Contributor'),
    (3, 'Funding Agency'),
    (3, 'Additional Metadata'),
    (3, 'Readme File')
ON CONFLICT (idartifacttype, typename) DO NOTHING;

COMMIT;
