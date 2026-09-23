-- Aurora Serverless v2 target schema (AWS Migration Plan, Section 5.1 and 10, step 3).
--
-- Identical structure to backend/database/schema.sql (same engine, same
-- tables, same recursive-CTE-friendly relationships - a pure vector store
-- would lose that), with one deliberate difference: `embedding` is
-- vector(1024) instead of vector(1792), because Amazon Titan Text
-- Embeddings V2 output dimension is 1024 (Section 5.2's recommended value
-- for retrieval-quality parity), not OpenAI's matryoshka-truncated 1792.
-- OpenAI and Titan embedding spaces are not comparable, so this is a new
-- schema populated by a full corpus re-embed
-- (backend/database/migrate_to_bedrock.py), not an in-place ALTER of the
-- existing Azure database.
--
-- Apply it with the migration script, which runs it one statement at a time
-- over the RDS Data API (the Data API rejects multi-statement SQL, and
-- psql cannot reach Aurora directly - the cluster has no public endpoint):
--
--   python backend/database/migrate_to_bedrock.py --apply-schema
--
-- Every statement is IF NOT EXISTS, so re-running it is harmless.
-- Keep semicolons out of comments: the script splits statements on ";".

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS TBLArtifactTypes (
    idArtifactType SERIAL PRIMARY KEY,
    TypeName TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS TBLArtifacts (
    idArtifact SERIAL PRIMARY KEY,
    idArtifactType INTEGER REFERENCES TBLArtifactTypes(idArtifactType),
    Title TEXT NOT NULL,
    URL TEXT UNIQUE NOT NULL,
    idArtifactParent INTEGER REFERENCES TBLArtifacts(idArtifact) ON DELETE CASCADE,
    summary_data JSONB,
    metadata JSONB,
    embedding vector(1024),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    isActive BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_artifact_type ON TBLArtifacts(idArtifactType);
CREATE INDEX IF NOT EXISTS idx_artifact_parent ON TBLArtifacts(idArtifactParent);
CREATE INDEX IF NOT EXISTS idx_artifact_embedding ON TBLArtifacts USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS TBLChunkTypes (
    idChunkType SERIAL PRIMARY KEY,
    idArtifactType INTEGER REFERENCES TBLArtifactTypes(idArtifactType),
    TypeName TEXT NOT NULL,
    CONSTRAINT unique_chunk_type_per_artifact UNIQUE (idArtifactType, TypeName)
);

CREATE TABLE IF NOT EXISTS TBLChunks (
    idChunk SERIAL PRIMARY KEY,
    idArtifact INTEGER REFERENCES TBLArtifacts(idArtifact) ON DELETE CASCADE,
    idChunkType INTEGER REFERENCES TBLChunkTypes(idChunkType),
    idChunkParent INTEGER REFERENCES TBLChunks(idChunk) ON DELETE CASCADE,
    "order" INTEGER,
    chunk_text TEXT,
    embedding vector(1024),
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_chunk_artifact ON TBLChunks(idArtifact);
CREATE INDEX IF NOT EXISTS idx_chunk_type ON TBLChunks(idChunkType);
CREATE INDEX IF NOT EXISTS idx_chunk_embedding ON TBLChunks USING hnsw (embedding vector_cosine_ops);
