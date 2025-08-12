-- Extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Hierarchical URLs Table
CREATE TABLE TBLURLs (
    idURL SERIAL PRIMARY KEY,
    URL TEXT NOT NULL,
    idURLParent INTEGER REFERENCES TBLURLs(idURL),
    Name TEXT NOT NULL,
    summary_data JSONB,
    embedding vector(1792)
);

-- HNSW index for TBLURLs
CREATE INDEX ON TBLURLs USING hnsw (embedding vector_cosine_ops);

-
-- Content Types Table
CREATE TABLE TBLContentTypes (
    idType SERIAL PRIMARY KEY,
    TypeName TEXT NOT NULL
);

-- Fragment content table
CREATE TABLE TBLContent (
    idContent SERIAL PRIMARY KEY,
    idURL INTEGER REFERENCES TBLURLs(idURL),
    idType INTEGER REFERENCES TBLContentTypes(idType),
    "order" INTEGER,
    Content TEXT,
    embedding vector(1792)
);

-- HNSW index for TBLContent
CREATE INDEX ON TBLContent USING hnsw (embedding vector_cosine_ops);

-- Tags table
CREATE TABLE TBLTags (
    idTag SERIAL PRIMARY KEY,
    Tag TEXT NOT NULL
);

-- URL-Tags relationship table
CREATE TABLE TRLURLTags (
    idURL INTEGER REFERENCES TBLURLs(idURL),
    idTag INTEGER REFERENCES TBLTags(idTag),
    PRIMARY KEY (idURL, idTag)
);
