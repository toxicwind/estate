//! keep-genkey — one-time operator tool: prints a fresh age identity.
//!
//! Store the secret key in your vault (or KEEP_AGE_KEY_FILE). It is printed
//! once, to stdout, by the operator — the service never logs or prints it.

use age::secrecy::ExposeSecret;

fn main() {
    let id = age::x25519::Identity::generate();
    println!("KEEP_AGE_IDENTITY={}", id.to_string().expose_secret());
    println!("KEEP_AGE_RECIPIENT={}", id.to_public());
}
