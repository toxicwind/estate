#!/usr/bin/env perl
# ble-lint.pl -- Lint a ble.sh config (~/.blerc) against the options that
# actually exist in your *installed* ble.sh. The valid-option list is
# discovered dynamically at runtime by scanning the ble.sh source, so it
# never goes stale.
#
# Usage:
#   perl ble-lint.pl                      # lint ~/.blerc, read-only report
#   perl ble-lint.pl --fix                # comment out invalid bleopt lines
#                                         # (backup saved as <config>.bak-TIMESTAMP)
#   perl ble-lint.pl --config FILE --blesh-dir DIR
#
# Exit status: 0 = no invalid options found, 1 = some found, 2 = usage/error.

use strict;
use warnings;
use Getopt::Long qw(GetOptions);
use File::Find   qw(find);
use File::Copy   qw(copy);
use File::Path   qw(make_path);

my ($blesh_dir, $config, $fix, $help);
GetOptions(
    'blesh-dir=s' => \$blesh_dir,
    'config=s'    => \$config,
    'fix'         => \$fix,
    'help'        => \$help,
) or do { print STDERR "Try --help.\n"; exit 2 };

if ($help) {
    print "Usage: $0 [--config FILE] [--blesh-dir DIR] [--fix]\n";
    exit 0;
}

$blesh_dir //= "$ENV{HOME}/.local/share/blesh";
$config    //= "$ENV{HOME}/.blerc";

die "error: ble.sh directory not found: $blesh_dir\n" unless -d $blesh_dir;
die "error: config file not found: $config\n"         unless -f $config;

#---------------------------------------------------------------------------
# 1. Dynamically discover every option name the installed ble.sh knows.
#    Defaults are declared in the source as  bleopt name=value  /
#    bleopt name:=value  (':=' appends), and the shipped blerc.template
#    documents them as  #bleopt name=value .
#---------------------------------------------------------------------------
my %valid;
find(
    sub {
        return unless -f $_;
        return unless /\.sh\z/ || $_ eq 'blerc.template' || $_ eq 'ble.sh';
        open my $fh, '<', $_ or do {
            warn "warning: cannot read $File::Find::name: $!\n";
            return;
        };
        while (my $line = <$fh>) {
            while ($line =~ /\bbleopt\s+([a-z][a-z0-9_]*):?=/g) {
                $valid{$1} = 1;
            }
        }
        close $fh;
    },
    $blesh_dir,
);

my @valid = sort keys %valid;
printf "Discovered %d valid bleopt options from %s\n", scalar(@valid), $blesh_dir;

#---------------------------------------------------------------------------
# 2. Scan the config and flag 'bleopt name=...' lines with unknown names.
#---------------------------------------------------------------------------
open my $in, '<', $config or die "error: cannot read $config: $!\n";
my @lines  = <$in>;
close $in;

my (@bad, @good);
for my $i (0 .. $#lines) {
    my $ln  = $i + 1;
    my $txt = $lines[$i];
    next if $txt =~ /^\s*#/;                       # already commented
    next unless $txt =~ /^\s*bleopt\s+([a-z][a-z0-9_]*):?=/;
    my $name = $1;
    if ($valid{$name}) { push @good, $name; next; }
    push @bad, [$ln, $name, $txt];
}

#---------------------------------------------------------------------------
# 3. Report (and optionally fix).
#---------------------------------------------------------------------------
if (@bad) {
    print "\nINVALID bleopt options in $config:\n";
    for my $b (@bad) {
        my ($ln, $name, $txt) = @$b;
        chomp $txt;
        printf "  line %-4d %-28s %s\n", $ln, $name, $txt;
    }
} else {
    print "All bleopt options in $config are valid.\n";
}

printf "\nSummary: %d valid option lines, %d invalid.\n", scalar(@good), scalar(@bad);

exit 0 unless $fix && @bad;

my $bak = sprintf '%s.bak-%04d%02d%02d-%02d%02d%02d',
    $config, (localtime)[5] + 1900, (localtime)[4] + 1, (localtime)[3,2,1,0];
copy($config, $bak) or die "error: backup failed: $!\n";
print "Backup written to $bak\n";

my %bad_line = map { $_->[0] => 1 } @bad;
for my $i (0 .. $#lines) {
    if ($bad_line{$i + 1}) {
        $lines[$i] =~ s/^(\s*)/$1# [ble-lint] unknown option, commented out: /;
    }
}

open my $out, '>', $config or die "error: cannot write $config: $!\n";
print {$out} @lines;
close $out;
print "$config updated: @{[scalar @bad]} line(s) commented out.\n";

exit 1;
