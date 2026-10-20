CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS "KnowledgeChunks" (
    "Id" uuid PRIMARY KEY,
    "SourceKey" text NOT NULL,
    "Title" text NOT NULL,
    "ChunkIndex" integer NOT NULL,
    "Content" text NOT NULL,
    "Embedding" vector(768) NOT NULL,
    "ContentHash" text NOT NULL,
    "UpdatedAt" timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT "UQ_KnowledgeChunks_Source_Chunk" UNIQUE ("SourceKey", "ChunkIndex")
);

CREATE INDEX IF NOT EXISTS "IX_KnowledgeChunks_SourceKey"
    ON "KnowledgeChunks" ("SourceKey");

CREATE INDEX IF NOT EXISTS "IX_KnowledgeChunks_Embedding"
    ON "KnowledgeChunks"
    USING hnsw ("Embedding" vector_cosine_ops);
