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
    URL TEXT UNIQUE NOT NULL,
    idArtifactParent INTEGER REFERENCES TBLArtifacts(idArtifact) ON DELETE CASCADE,
    summary_data JSONB,
    metadata JSONB,
    embedding vector(1792),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- B-Tree Index for frequent joins and lookups
CREATE INDEX idx_artifact_type ON TBLArtifacts(idArtifactType);
CREATE INDEX idx_artifact_parent ON TBLArtifacts(idArtifactParent);

-- HNSW index for vector search
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
    embedding vector(1792)
);

-- B-Tree Indexes for performance
CREATE INDEX idx_chunk_artifact ON TBLChunks(idArtifact);
CREATE INDEX idx_chunk_type ON TBLChunks(idChunkType);

-- HNSW index for granular vector search 
CREATE INDEX ON TBLChunks USING hnsw (embedding vector_cosine_ops);