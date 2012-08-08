#!/usr/bin/perl

use strict;
use warnings;

open(RESULTS, ">/home/egoetz/TwoSpect/UL/results.dat") or die "Cannot write to /home/egoetz/TwoSpect/UL/results.dat $!";

for(my $ii=0; $ii<100; $ii++) {
   open(INJECTEDVALS, "/home/egoetz/TwoSpect/UL/$ii/injections.dat") or die "Cannot open /home/egoetz/TwoSpect/UL/$ii/injections.dat $!";
   my @injections = <INJECTEDVALS>;
   my @injections2;
   my $jj;
   for($jj=0; $jj<10; $jj++) {
      push(@injections2, $injections[$jj]);
   }
   close(INJECTEDVALS);
   @injections2 = reverse @injections2;
   
   $jj = 0;
   foreach my $injection (@injections) {
      $injection = chomp($injection);
      
      open(ULFILE, "/home/egoetz/TwoSpect/efficiency/$ii/uls_$jj.txt") or die "Cannot open /home/egoetz/TwoSpect/efficiency/$ii/uls_$jj.txt $!";
      my $ul = chomp(<ULFILE>);
      
      print RESULTS "$injection $ul\n";
      
      close(ULFILE);
      $jj++;
   }
}

close(RESULTS);
