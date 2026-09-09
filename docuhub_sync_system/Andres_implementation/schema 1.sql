-- Extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Artifact Types Table
CREATE TABLE TBLArtifactTypes (
    idArtifactType SERIAL PRIMARY KEY,
    TypeName TEXT NOT NULL UNIQUE
);

-- 2. Hierarchical Artifacts Table
CREATE TABLE TBLArtifacts (
    idArtifact SERIAL PRIMARY KEY,
    idArtifactType INTEGER REFERENCES TBLArtifactTypes(idArtifactType),
    Title TEXT NOT NULL,
    URL TEXT NOT NULL,
    idArtifactParent INTEGER REFERENCES TBLArtifacts(idArtifact) ON DELETE CASCADE,
    summary_data JSONB,
    metadata JSONB,
    embedding vector(1792),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    isActive BOOLEAN NOT NULL DEFAULT TRUE
);

-- Only one active artifact per URL; inactive duplicates are allowed
CREATE UNIQUE INDEX idx_artifact_url_active ON TBLArtifacts(URL) WHERE isActive = TRUE;

-- B-Tree Index for frequent joins and lookups
CREATE INDEX idx_artifact_type ON TBLArtifacts(idArtifactType);
CREATE INDEX idx_artifact_parent ON TBLArtifacts(idArtifactParent);
CREATE INDEX idx_artifact_active ON TBLArtifacts(isActive);

-- HNSW index for vector search (only active artifacts)
CREATE INDEX ON TBLArtifacts USING hnsw (embedding vector_cosine_ops);

-- 3. Chunk Types Table
CREATE TABLE TBLChunkTypes (
    idChunkType SERIAL PRIMARY KEY,
    idArtifactType INTEGER REFERENCES TBLArtifactTypes(idArtifactType),
    TypeName TEXT NOT NULL,
    CONSTRAINT unique_chunk_type_per_artifact UNIQUE (idArtifactType, TypeName)
);

-- 4.Chunk content table
CREATE TABLE TBLChunks (
    idChunk SERIAL PRIMARY KEY,
    idArtifact INTEGER REFERENCES TBLArtifacts(idArtifact) ON DELETE CASCADE,
    idChunkType INTEGER REFERENCES TBLChunkTypes(idChunkType),
    idChunkParent INTEGER REFERENCES TBLChunks(idChunk) ON DELETE CASCADE,
    "order" INTEGER,
    chunk_text TEXT,
    embedding vector(1792),
    metadata JSONB
);

-- B-Tree Indexes for performance
CREATE INDEX idx_chunk_artifact ON TBLChunks(idArtifact);
CREATE INDEX idx_chunk_type ON TBLChunks(idChunkType);

-- HNSW index for granular vector search
CREATE INDEX ON TBLChunks USING hnsw (embedding vector_cosine_ops);

-- Seed the identifiers and names used by the Azure-aligned schema.
INSERT INTO TBLArtifactTypes (idArtifactType, TypeName)
VALUES
    (1, 'DocuHub Page'),
    (2, 'Publication'),
    (3, 'Dataset'),
    (4, 'GitHub Repository'),
    (5, 'Course'),
    (6, 'Presentation')
ON CONFLICT DO NOTHING;

SELECT setval(
    pg_get_serial_sequence('tblartifacttypes', 'idartifacttype'),
    (SELECT MAX(idArtifactType) FROM TBLArtifactTypes)
);

INSERT INTO TBLChunkTypes (idArtifactType, TypeName)
VALUES
    (1, 'Section'),
    (1, 'Subsection'),
    (1, 'Subsubsection'),
    (4, 'Project Overview'),
    (4, 'Installation Setup'),
    (4, 'Usage Examples'),
    (4, 'Repository Structure'),
    (4, 'Contributing Guidelines'),
    (4, 'License Citation'),
    (4, 'Documentation Section'),
    (4, 'Notebook Section'),
    (4, 'Configuration / Deployment'),
    (4, 'Change Log / Release Notes')
ON CONFLICT DO NOTHING;
