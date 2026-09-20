p = '/home/toxic/mesh-bruteforce-20260914/tau/engine/crates/pi-vcs/src/git/mutate.rs'
s = open(p).read()
anchor = '\t#[test]\n\tfn mutate_stage_commit_amend_and_empty() {'
assert s.count(anchor) == 1
test = '''\t#[test]
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
s = s.replace(anchor, test + anchor)
open(p, 'w').write(s)
print('probe added')
