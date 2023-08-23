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
    src TEXT DEFAULT '',
    title TEXT DEFAULT ''
);

CREATE TABLE simon_paragraphs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    hash TEXT NOT NULL,
    uid TEXT NOT NULL,
    text TEXT DEFAULT '',
    embedding vector(1536) NOT NULL,
    src TEXT DEFAULT '',
    title TEXT DEFAULT '',
    tf FLOAT DEFAULT 0.0,
    seq INTEGER DEFAULT 0,
    total INTEGER DEFAULT 0
);

