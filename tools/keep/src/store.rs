//! SQLite persistence. Only age ciphertext touches disk.

use rusqlite::{params, Connection};
use serde::Serialize;
use std::sync::Mutex;
use zeroize::Zeroizing;

use crate::crypto;

pub struct SecretStore {
    conn: Mutex<Connection>,
    identity: age::x25519::Identity,
}

#[derive(Debug, Serialize, Clone)]
pub struct SecretMeta {
    pub name: String,
    pub purpose: Option<String>,
    pub created_at: String,
    pub updated_at: String,
    pub rotated_at: Option<String>,
    pub version: i64,
}

fn now() -> String {
    chrono::Utc::now().to_rfc3339_opts(chrono::SecondsFormat::Secs, true)
}

impl SecretStore {
    pub fn open(path: &str, identity: age::x25519::Identity) -> anyhow::Result<Self> {
        let conn = Connection::open(path)?;
        conn.execute_batch(
            "CREATE TABLE IF NOT EXISTS secrets (
                name        TEXT PRIMARY KEY,
                purpose     TEXT,
                ciphertext  BLOB NOT NULL,
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL,
                rotated_at  TEXT,
                version     INTEGER NOT NULL DEFAULT 1
            );",
        )?;
        Ok(Self {
            conn: Mutex::new(conn),
            identity,
        })
    }

    /// Insert or replace a secret. Logs the name only — never the value.
    pub fn put(&self, name: &str, purpose: Option<&str>, value: Zeroizing<String>) -> anyhow::Result<SecretMeta> {
        let ct = crypto::encrypt_value(&self.identity, &value)?;
        let ts = now();
        let conn = self.conn.lock().unwrap();
        let n: i64 = conn.query_row(
            "SELECT COUNT(*) FROM secrets WHERE name = ?1",
            params![name],
            |r| r.get(0),
        )?;
        if n == 0 {
            conn.execute(
                "INSERT INTO secrets (name, purpose, ciphertext, created_at, updated_at, version)
                 VALUES (?1, ?2, ?3, ?4, ?4, 1)",
                params![name, purpose, ct, ts],
            )?;
        } else {
            conn.execute(
                "UPDATE secrets SET purpose = COALESCE(?2, purpose), ciphertext = ?3,
                                  updated_at = ?4 WHERE name = ?1",
                params![name, purpose, ct, ts],
            )?;
        }
        drop(conn);
        tracing::info!(secret = %name, "secret stored");
        self.meta(name)
    }

    /// Fetch and decrypt a secret value. Caller must be authenticated (enforced in api).
    pub fn get_value(&self, name: &str) -> anyhow::Result<Option<Zeroizing<String>>> {
        let conn = self.conn.lock().unwrap();
        let ct: Option<Vec<u8>> = conn
            .query_row(
                "SELECT ciphertext FROM secrets WHERE name = ?1",
                params![name],
                |r| r.get(0),
            )
            .optional_anyhow()?;
        drop(conn);
        match ct {
            None => Ok(None),
            Some(bytes) => {
                let v = crypto::decrypt_value(&self.identity, &bytes)?;
                tracing::info!(secret = %name, "secret retrieved");
                Ok(Some(v))
            }
        }
    }

    /// Rotate: replace value, bump version, stamp rotated_at.
    pub fn rotate(&self, name: &str, value: Zeroizing<String>) -> anyhow::Result<Option<SecretMeta>> {
        let ct = crypto::encrypt_value(&self.identity, &value)?;
        let ts = now();
        let conn = self.conn.lock().unwrap();
        let n = conn.execute(
            "UPDATE secrets SET ciphertext = ?2, updated_at = ?3, rotated_at = ?3,
                              version = version + 1 WHERE name = ?1",
            params![name, ct, ts],
        )?;
        drop(conn);
        if n == 0 {
            return Ok(None);
        }
        tracing::info!(secret = %name, "secret rotated");
        Ok(Some(self.meta(name)?))
    }

    /// Metadata list — names, purposes, dates. Never values.
    pub fn list_meta(&self) -> anyhow::Result<Vec<SecretMeta>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT name, purpose, created_at, updated_at, rotated_at, version
             FROM secrets ORDER BY name",
        )?;
        let rows = stmt.query_map([], |r| {
            Ok(SecretMeta {
                name: r.get(0)?,
                purpose: r.get(1)?,
                created_at: r.get(2)?,
                updated_at: r.get(3)?,
                rotated_at: r.get(4)?,
                version: r.get(5)?,
            })
        })?;
        rows.collect::<Result<Vec<_>, _>>().map_err(|e| e.into())
    }

    fn meta(&self, name: &str) -> anyhow::Result<SecretMeta> {
        let conn = self.conn.lock().unwrap();
        conn.query_row(
            "SELECT name, purpose, created_at, updated_at, rotated_at, version
             FROM secrets WHERE name = ?1",
            params![name],
            |r| {
                Ok(SecretMeta {
                    name: r.get(0)?,
                    purpose: r.get(1)?,
                    created_at: r.get(2)?,
                    updated_at: r.get(3)?,
                    rotated_at: r.get(4)?,
                    version: r.get(5)?,
                })
            },
        )
        .map_err(|e| e.into())
    }
}

trait OptionalAnyhow<T> {
    fn optional_anyhow(self) -> anyhow::Result<Option<T>>;
}
impl<T> OptionalAnyhow<T> for Result<T, rusqlite::Error> {
    fn optional_anyhow(self) -> anyhow::Result<Option<T>> {
        match self {
            Ok(v) => Ok(Some(v)),
            Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
            Err(e) => Err(e.into()),
        }
    }
}
