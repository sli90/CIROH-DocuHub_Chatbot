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
-- Run this once against the new Aurora cluster (Section 10, step 3), via
-- the RDS Data API (psql cannot reach Aurora directly - Section 3.3,
-- "no VPC-attached Lambda" applies to psql too, since the cluster has no
-- public endpoint):
--
--   aws rds-data execute-statement \
--     --resource-arn "$AURORA_CLUSTER_ARN" \
--     --secret-arn "$AURORA_SECRET_ARN" \
--     --database "$AURORA_DATABASE" \
--     --sql "$(cat backend/database/schema_aws.sql)"

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE TBLArtifactTypes (
    idArtifactType SERIAL PRIMARY KEY,
    TypeName TEXT NOT NULL UNIQUE
);

CREATE TABLE TBLArtifacts (
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

CREATE INDEX idx_artifact_type ON TBLArtifacts(idArtifactType);
CREATE INDEX idx_artifact_parent ON TBLArtifacts(idArtifactParent);
CREATE INDEX ON TBLArtifacts USING hnsw (embedding vector_cosine_ops);

CREATE TABLE TBLChunkTypes (
    idChunkType SERIAL PRIMARY KEY,
    idArtifactType INTEGER REFERENCES TBLArtifactTypes(idArtifactType),
    TypeName TEXT NOT NULL,
    CONSTRAINT unique_chunk_type_per_artifact UNIQUE (idArtifactType, TypeName)
);

CREATE TABLE TBLChunks (
    idChunk SERIAL PRIMARY KEY,
    idArtifact INTEGER REFERENCES TBLArtifacts(idArtifact) ON DELETE CASCADE,
    idChunkType INTEGER REFERENCES TBLChunkTypes(idChunkType),
    idChunkParent INTEGER REFERENCES TBLChunks(idChunk) ON DELETE CASCADE,
    "order" INTEGER,
    chunk_text TEXT,
    embedding vector(1024),
    metadata JSONB
);

CREATE INDEX idx_chunk_artifact ON TBLChunks(idArtifact);
CREATE INDEX idx_chunk_type ON TBLChunks(idChunkType);
CREATE INDEX ON TBLChunks USING hnsw (embedding vector_cosine_ops);
