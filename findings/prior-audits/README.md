Prior audits harvested from /tmp and $HOME before any cleanup.
Nothing was deleted during harvest — sources remain in /tmp until natural eviction.
The cleanup ladder (backup-repo kills, stale archives) only proceeds against
this committed inventory; deletions require a committed manifest first.
