-- Create user_sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id VARCHAR PRIMARY KEY,
    user_identifier VARCHAR,
    context TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create index on user_identifier
CREATE INDEX IF NOT EXISTS ix_user_sessions_user_identifier ON user_sessions (user_identifier);

-- Create conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id VARCHAR PRIMARY KEY,
    user_session_id VARCHAR NOT NULL,
    topic VARCHAR,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (user_session_id) REFERENCES user_sessions (id)
);

-- Create messages table
CREATE TABLE IF NOT EXISTS messages (
    id VARCHAR PRIMARY KEY,
    conversation_id VARCHAR NOT NULL,
    message_type VARCHAR NOT NULL,
    content TEXT NOT NULL,
    message_metadata TEXT,
    sequence_number INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
); 