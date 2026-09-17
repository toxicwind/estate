//! age encryption layer. The master identity lives outside the repo
//! (KEEP_AGE_IDENTITY or KEEP_AGE_KEY_FILE). Ciphertext is what hits SQLite.
//!
//! Generate an identity once with the `age-keygen` CLI (rage package) and
//! store the secret key in your vault — the service only ever reads it.

use std::io::{Read, Write};
use zeroize::Zeroizing;

/// Load the age identity from env or key file. Fails closed.
pub fn load_identity() -> anyhow::Result<age::x25519::Identity> {
    let key: Zeroizing<String> = if let Ok(k) = std::env::var("KEEP_AGE_IDENTITY") {
        Zeroizing::new(k)
    } else if let Ok(p) = std::env::var("KEEP_AGE_KEY_FILE") {
        let raw = std::fs::read_to_string(&p)
            .map_err(|e| anyhow::anyhow!("reading KEEP_AGE_KEY_FILE: {e}"))?;
        Zeroizing::new(raw.trim().to_string())
    } else {
        anyhow::bail!("no age identity: set KEEP_AGE_IDENTITY or KEEP_AGE_KEY_FILE");
    };
    key.parse::<age::x25519::Identity>()
        .map_err(|e| anyhow::anyhow!("parsing age identity: {e}"))
}

/// Encrypt plaintext to our own recipient. Returns opaque ciphertext bytes.
pub fn encrypt_value(
    identity: &age::x25519::Identity,
    plaintext: &Zeroizing<String>,
) -> anyhow::Result<Vec<u8>> {
    let recipient = identity.to_public();
    let encryptor =
        age::Encryptor::with_recipients([&recipient as &dyn age::Recipient].into_iter())
            .map_err(|e| anyhow::anyhow!("age encryptor: {e}"))?;
    let mut out = Vec::new();
    let mut writer = encryptor
        .wrap_output(&mut out)
        .map_err(|e| anyhow::anyhow!("age wrap: {e}"))?;
    writer
        .write_all(plaintext.as_bytes())
        .map_err(|e| anyhow::anyhow!("age write: {e}"))?;
    writer
        .finish()
        .map_err(|e| anyhow::anyhow!("age finish: {e}"))?;
    Ok(out)
}

/// Decrypt ciphertext back into a zeroizing wrapper. Plaintext never escapes it.
pub fn decrypt_value(
    identity: &age::x25519::Identity,
    ciphertext: &[u8],
) -> anyhow::Result<Zeroizing<String>> {
    let decryptor =
        age::Decryptor::new(ciphertext).map_err(|e| anyhow::anyhow!("age decryptor: {e}"))?;
    let mut reader = decryptor
        .decrypt(std::iter::once(identity as &dyn age::Identity))
        .map_err(|e| anyhow::anyhow!("age decrypt: {e}"))?;
    let mut buf = Vec::new();
    reader
        .read_to_end(&mut buf)
        .map_err(|e| anyhow::anyhow!("age read: {e}"))?;
    let s = String::from_utf8(buf).map_err(|e| anyhow::anyhow!("utf8: {e}"))?;
    Ok(Zeroizing::new(s))
}
