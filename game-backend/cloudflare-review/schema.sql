CREATE TABLE IF NOT EXISTS review_login_attempts (
  bucket TEXT PRIMARY KEY,
  attempts INTEGER NOT NULL,
  expires_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS review_login_expiry ON review_login_attempts(expires_at);
