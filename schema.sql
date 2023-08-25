CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;


CREATE TABLE simon_cache (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    uri TEXT NOT NULL,
    hash TEXT NOT NULL,
    uid TEXT NOT NULL
);

CREATE TABLE simon_fulltext (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    hash TEXT NOT NULL,
    uid TEXT NOT NULL,
    text TEXT DEFAULT '',
    text_fuzzy tsvector GENERATED ALWAYS AS (to_tsvector('english', text)) STORED,
    src TEXT DEFAULT '',
    title TEXT DEFAULT '',
    title_fuzzy tsvector GENERATED ALWAYS AS (to_tsvector('english', title)) STORED
);

CREATE TABLE simon_paragraphs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    hash TEXT NOT NULL,
    uid TEXT NOT NULL,
    text TEXT DEFAULT '',
    text_fuzzy tsvector GENERATED ALWAYS AS (to_tsvector('english', text)) STORED,
    embedding vector(1536) NOT NULL,
    src TEXT DEFAULT '',
    title TEXT DEFAULT '',
    title_fuzzy tsvector GENERATED ALWAYS AS (to_tsvector('english', title)) STORED,
    tf FLOAT DEFAULT 0.0,
    seq INTEGER DEFAULT 0,
    total INTEGER DEFAULT 0
);

CREATE INDEX simon_paragraphs_embedding_cosine_idx ON simon_paragraphs USING ivfflat (embedding vector_cosine_ops) WITH (lists = 200); 
CREATE INDEX simon_paragraphs_text_index ON simon_paragraphs USING GIN (text_fuzzy);
CREATE INDEX simon_paragraphs_chunk_index ON simon_paragraphs USING BTREE (seq);
CREATE INDEX simon_paragraphs_chunk_hash ON simon_paragraphs USING HASH (hash);
CREATE INDEX simon_paragraphs_title_index ON simon_paragraphs USING GIN (title_fuzzy);
CREATE INDEX simon_fulltext_text_index ON simon_fulltext USING GIN (text_fuzzy);
CREATE INDEX simon_fulltext_title_index ON simon_fulltext USING GIN (title_fuzzy);
