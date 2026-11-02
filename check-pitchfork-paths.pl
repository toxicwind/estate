#!/usr/bin/perl
# check-pitchfork-paths.pl — scan all pitchfork daemon configs for broken
# run/dir paths. Uses state.toml (the applied config pitchfork parsed) as the
# authoritative source: each block carries cmd = [...], dir = "...", status.
use strict;
use warnings;

my $state_file = "/home/toxic/.local/state/pitchfork/state.toml";
open my $fh, "<", $state_file or die "cannot open $state_file: $!\n";
local $/ = "\n[daemons.";  # each chunk starts at a [daemons."id"] header
my @broken;
while (<$fh>) {
    my $chunk = $_;
    my ($id) = $chunk =~ /^"(.*?)"/;
    next unless defined $id;
    my ($dir)     = $chunk =~ /^dir\s*=\s*"([^"]*)"/m;
    my ($status)  = $chunk =~ /^status\s*=\s*"([^"]*)"/m;
    my $cmdline   = "";
    my $arr = "";
    if ($chunk =~ /^cmd\s*=\s*\[(.*?)\]/ms) {
        $arr = $1;
        ($cmdline) = $arr =~ /"([^"]*)"/s;  # first argv element (the program)
    }
    my $prog = $cmdline;
    # if program is "exec" or "env" or "export", take the next real token
    if ($prog =~ /^(?:exec|env|export)$/) {
        my @toks = ($arr =~ /"([^"]*)"/g) if $arr;
        for my $t (@toks) {
            next if $t =~ /^(?:exec|env|export)$/ || $t =~ /=/;
            $prog = $t;
            last;
        }
    }
    my $ok = 1;
    my $reason = "";
    if (defined $dir && ! -d $dir) { $ok = 0; $reason .= "dir MISSING($dir) "; }
    if ($prog && $prog !~ /^\//) {
        if ($prog =~ m{^\./}) {
            # relative run path — resolve against daemon dir
            my $abs = defined $dir ? "$dir/$prog" : $prog;
            if (! -e $abs) { $ok = 0; $reason .= "run-file MISSING($abs) "; }
        } elsif (system("command -v '$prog' >/dev/null 2>&1") != 0) {
            $ok = 0; $reason .= "run-exe MISSING($prog) ";
        }
    } elsif ($prog && ! -e $prog) {
        $ok = 0; $reason .= "run-file MISSING($prog) ";
    }
    if (!$ok) {
        push @broken, sprintf("%-34s %-10s %s", $id, $status||"?", $reason);
    }
}
close $fh;
print "BROKEN DAEMON CONFIGS (state.toml applied view):\n";
print join("\n", @broken), "\n";
print "\n", scalar(@broken), " broken daemon(s).\n";