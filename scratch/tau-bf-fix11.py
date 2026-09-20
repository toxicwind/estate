#!/usr/bin/env python3
"""Fix batch 11: robust date parsing for commit author dates."""
import sys

BASE = "/home/toxic/tau-bf-20260914/tau/engine"
p = f"{BASE}/crates/pi-vcs/src/git/mutate.rs"

with open(p) as f:
    c = f.read()

# Replace gix::date::parse with a helper that also handles RFC 3339
old = """\t\t\tlet time = match &author.date {
\t\t\t\tSome(date) => {
\t\t\t\t\tgix::date::parse(date, None).map_err(|err| Error::backend("git commit", err))?
\t\t\t\t},
\t\t\t\tNone => gix::date::Time::now_local_or_utc(),
\t\t\t};"""

new = """\t\t\tlet time = match &author.date {
\t\t\t\tSome(date) => parse_commit_date(date)
\t\t\t\t\t.map_err(|err| Error::backend("git commit", err))?,
\t\t\t\tNone => gix::date::Time::now_local_or_utc(),
\t\t\t};"""

if c.count(old) != 1:
    print(f"FAIL: found {c.count(old)}x")
    sys.exit(1)
c = c.replace(old, new)

# Add the parse_commit_date helper function before commit_create
# Find the function containing this code and add helper before it
helper = """
/// Parse a commit author date string.
///
/// Tries `gix::date::parse` first (git formats), then falls back to a
/// minimal RFC 3339 parser (`YYYY-MM-DDTHH:MM:SSZ`) for ISO 8601 inputs
/// like `"2020-01-02T03:04:05Z"`.
fn parse_commit_date(input: &str) -> Result<gix::date::Time, gix::date::parse::Error> {
    if let Ok(time) = gix::date::parse(input, None) {
        return Ok(time);
    }
    // Minimal RFC 3339: YYYY-MM-DDTHH:MM:SSZ (UTC only)
    let input = input.trim();
    if let Some(stripped) = input.strip_suffix('Z') {
        let parts: Vec<&str> = stripped.split('T').collect();
        if parts.len() == 2 {
            let date_parts: Vec<&str> = parts[0].split('-').collect();
            let time_parts: Vec<&str> = parts[1].split(':').collect();
            if date_parts.len() == 3 && time_parts.len() == 3 {
                if let (Ok(y), Ok(m), Ok(d), Ok(h), Ok(min), Ok(s)) = (
                    date_parts[0].parse::<i32>(),
                    date_parts[1].parse::<u32>(),
                    date_parts[2].parse::<u32>(),
                    time_parts[0].parse::<u32>(),
                    time_parts[1].parse::<u32>(),
                    time_parts[2].parse::<u32>(),
                ) {
                    // Days from civil date (Howard Hinnant's algorithm)
                    let y = if m <= 2 { y - 1 } else { y };
                    let era = y.div_euclid(400);
                    let yoe = y.rem_euclid(400) as u32;
                    let mp = (m + 9).rem_euclid(12);
                    let doy = (153 * mp + 2) / 5 + d - 1;
                    let doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
                    let days = era * 146097 + doe as i32 - 719468;
                    let secs = days as i64 * 86400 + h as i64 * 3600 + min as i64 * 60 + s as i64;
                    return Ok(gix::date::Time::new(secs, 0));
                }
            }
        }
    }
    Err(gix::date::parse::Error::InvalidDateString { input: input.into() })
}

"""

# Insert before the function that contains commit_create
# Find "fn commit_create" or similar
if "fn parse_commit_date" not in c:
    # Insert before the first occurrence of the commit_create function
    # Let's find a good anchor - insert before "impl GitRepo" or similar
    # Actually, insert at the top of the file after imports
    lines = c.split('\n')
    # Find where to insert (after use statements)
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('use ') or line.startswith('pub use '):
            insert_idx = i + 1
    lines.insert(insert_idx, helper)
    c = '\n'.join(lines)

with open(p, "w") as f:
    f.write(c)
print("OK [parse_commit_date]")
print("FIX-11 DONE")
