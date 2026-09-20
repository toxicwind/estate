p = '/home/toxic/mesh-bruteforce-20260914/tau/engine/crates/pi-vcs/src/git/mutate.rs'
lines = open(p).readlines()
start = next(i for i, l in enumerate(lines) if l.startswith('fn parse_commit_date'))
end = next(i for i in range(start + 1, len(lines)) if lines[i] == '}\n')
print('replacing lines', start + 1, 'to', end + 1)
new_fn = '''fn parse_commit_date(input: &str) -> Result<gix::date::Time, gix::date::parse::Error> {
    if let Ok(time) = gix::date::parse(input, None) {
        return Ok(time);
    }
    let invalid = || gix::date::parse::Error::InvalidDateString { input: input.trim().into() };
    // Minimal RFC 3339: YYYY-MM-DDTHH:MM:SSZ (UTC only). Every field is
    // range-checked so syntactically numeric but impossible dates (month 13,
    // February 30, hour 25, ...) are rejected instead of silently wrapping
    // into unrelated timestamps.
    fn digits(part: &str, len: usize) -> Option<u32> {
        if part.len() == len && part.bytes().all(|b| b.is_ascii_digit()) {
            part.parse().ok()
        } else {
            None
        }
    }
    let stripped = input.trim().strip_suffix('Z').ok_or_else(invalid)?;
    let (date, clock) = stripped.split_once('T').ok_or_else(invalid)?;
    let mut dparts = date.split('-');
    let (year, month, day) = match (dparts.next(), dparts.next(), dparts.next(), dparts.next()) {
        (Some(y), Some(m), Some(d), None) => (
            digits(y, 4).ok_or_else(invalid)?,
            digits(m, 2).ok_or_else(invalid)?,
            digits(d, 2).ok_or_else(invalid)?,
        ),
        _ => return Err(invalid()),
    };
    let mut tparts = clock.split(':');
    let (hour, minute, second) = match (tparts.next(), tparts.next(), tparts.next(), tparts.next()) {
        (Some(h), Some(mi), Some(s), None) => (
            digits(h, 2).ok_or_else(invalid)?,
            digits(mi, 2).ok_or_else(invalid)?,
            digits(s, 2).ok_or_else(invalid)?,
        ),
        _ => return Err(invalid()),
    };
    if !(1..=12).contains(&month) || hour > 23 || minute > 59 || second > 59 {
        return Err(invalid());
    }
    let leap = year % 4 == 0 && (year % 100 != 0 || year % 400 == 0);
    let max_day = match month {
        2 if leap => 29,
        2 => 28,
        4 | 6 | 9 | 11 => 30,
        _ => 31,
    };
    if day == 0 || day > max_day {
        return Err(invalid());
    }
    // Days from civil date (Howard Hinnant's algorithm). Inputs are
    // validated above, so this cannot wrap or overflow.
    let y = i64::from(year) - i64::from(month <= 2);
    let era = y.div_euclid(400);
    let yoe = y.rem_euclid(400) as u32;
    let mp = (i64::from(month) + 9).rem_euclid(12) as u32;
    let doy = (153 * mp + 2) / 5 + day - 1;
    let doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    let days = era * 146097 + i64::from(doe) - 719468;
    let secs = days * 86400 + i64::from(hour) * 3600 + i64::from(minute) * 60 + i64::from(second);
    Ok(gix::date::Time::new(secs, 0))
}
'''
lines[start:end + 1] = [new_fn]
open(p, 'w').write(''.join(lines))
print('parse_commit_date replaced')
