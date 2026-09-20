p = '/home/toxic/mesh-bruteforce-20260914/tau/engine/crates/pi-vcs/src/git/mutate.rs'
s = open(p).read()
old_probe = '''\t#[test]
\tfn parse_commit_date_probe() {
\t\tfor input in [
\t\t\t"2020-01-02T03:04:05Z",
\t\t\t"2020-13-01T00:00:00Z",
\t\t\t"2020-01-01T24:00:00Z",
\t\t] {
\t\t\teprintln!("gix direct {input:?} => {:?}", gix::date::parse(input, None).map(|t| t.seconds));
\t\t\teprintln!("ours      {input:?} => {:?}", parse_commit_date(input).map(|t| t.seconds));
\t\t}
\t}

'''
assert s.count(old_probe) == 1
test = '''\t#[test]
\tfn parse_commit_date_validates_rfc3339_fields() {
\t\t// Sanity: a well-formed timestamp parses (2020-01-02T03:04:05Z).
\t\tassert_eq!(parse_commit_date("2020-01-02T03:04:05Z").unwrap().seconds, 1577934245);
\t\t// February 29 is valid on leap years ...
\t\tassert_eq!(parse_commit_date("2024-02-29T12:00:00Z").unwrap().seconds, 1709208000);
\t\tassert_eq!(parse_commit_date("2000-02-29T00:00:00Z").unwrap().seconds, 951782400);
\t\t// ... but not otherwise.
\t\tfor bad in [
\t\t\t"2021-02-29T00:00:00Z", // non-leap Feb 29
\t\t\t"1900-02-29T00:00:00Z", // century non-leap Feb 29
\t\t\t"2020-02-30T00:00:00Z", // Feb 30 never exists
\t\t\t"2020-13-01T00:00:00Z", // month 13
\t\t\t"2020-00-10T00:00:00Z", // month 0
\t\t\t"2020-01-00T00:00:00Z", // day 0
\t\t\t"2020-01-32T00:00:00Z", // day 32
\t\t\t"2020-04-31T00:00:00Z", // April 31
\t\t\t"2020-06-31T00:00:00Z", // June 31
\t\t\t"2020-01-01T24:00:00Z", // hour 24
\t\t\t"2020-01-01T23:60:00Z", // minute 60
\t\t\t"2020-01-01T23:59:60Z", // second 60
\t\t\t"2020-1-2T03:04:05Z",   // non-zero-padded date
\t\t\t"2020-01-02T3:04:05Z",  // non-zero-padded hour
\t\t\t"2020-01-02 03:04:05Z", // missing T separator
\t\t\t"2020-01-02T03:04:05",  // missing Z suffix
\t\t\t"2020-01-02T03:04:05+00:00", // offset suffix unsupported
\t\t\t"not-a-date",
\t\t] {
\t\t\tassert!(parse_commit_date(bad).is_err(), "{bad} should be rejected");
\t\t}
\t}

'''
s = s.replace(old_probe, test)
open(p, 'w').write(s)
print('date edge tests added')
