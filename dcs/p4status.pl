#!/usr/bin/perl

use strict;
use warnings;
use Cwd;

my $argc = @ARGV;

if ($argc != 1) { die "Usage: " . $0 . " ( show | kill )\n"; exit 1; }

my %process = ( 'p4d'      => 0,
                'p4zk'     => 0,
                'p4p'      => 0,
                'p4broker' => 0,
                #'t4.pl'    => 0,
                #'chmodder' => 0
              ); 
my $status = '';
if (defined($ARGV[0])) {
  $status = $ARGV[0];
}
  
my ($user, $pid, $p_name, @cmd) = ('', 0, '', ());

my @process_array = `ps -ef | grep p4`;
foreach(@process_array) {
    ($user, $pid) = split(/\s+/,$_);  
    $p_name = `ps -p $pid -o comm=`; 

    chomp($p_name); #removes the newline character
    if (defined($process{$p_name})) {
      $process{$p_name} += 1;
    }
    if ($p_name ne '' && $process{$p_name}) {
      if ($status eq 'kill') { 
        print "KILLED PID: $pid\n";
        print `pstree -a -p -n $pid`;
        `kill -9 $pid`;
      } elsif ($status eq 'show') {
        print "$p_name ($pid): Process #$process{$p_name}\n";
        print `pstree -a -p -n $pid`;
      }
    }
}
