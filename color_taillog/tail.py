#!/usr/bin/python
#Author: Stephen Moon
#Summary of Program: This program takes up to 7 keyword arguments and colorize the "tail -f" line
#which contains the specified keywords.
#

import sys, time

class TColor:

  PINK      = '\033[95m'
  BLUE      = '\033[94m'
  GREEN     = '\033[92m'
  YELLOW    = '\033[93m'
  ORANGE    = '\033[91m'
  BOLD      = '\033[1m'
  UNDERLINE = '\033[4m'
  ENDC      = '\033[0m'

class Tail( object ):
  
  def __init__( self, *args ):

    self.argv        = args[0]
    self.color_dict  = {}
    self.color_array = [ TColor.PINK, TColor.BLUE, TColor.GREEN, 
                         TColor.YELLOW, TColor.ORANGE, TColor.BOLD, TColor.UNDERLINE ]
    self.color_code  = { TColor.PINK:'PINK', TColor.BLUE:'BLUE', TColor.GREEN:'GREEN', 
                         TColor.YELLOW:'YELLOW', TColor.ORANGE:'ORANGE', TColor.BOLD:'BOLD', TColor.UNDERLINE:'UNDERLINE' } 

  def tail( self, f ):

    f.seek(0,2) #use offset of zero at file end
    while True:
      line = f.readline()
      if not line:
        time.sleep(0.1)
        continue
      yield line

  def create_dict( self ):

    for i, arg in enumerate(self.argv):
      self.color_dict[arg] = self.color_array[i]

    for k, v in sorted( self.color_dict.iteritems() ):
      print self.color_dict[k] + "Key: " + k + "\tColor: " + self.color_code[v],
      print TColor.ENDC

  def grep( self, lines ):

    for line in lines:
      color_on = False
      for arg in self.argv:
        if arg in line:
          color_on = True
          f_line = self.color_dict[arg] + line.strip() + TColor.ENDC +'\n'
          yield f_line
      if not color_on:
        yield line

def main():

  if len(sys.argv) < 3:
    print "Usage: %s <file_name> <filter_1...filter_7>" % sys.argv[0]
    sys.exit(1)

  file_name = sys.argv[1]
  args      = sys.argv[2:]

  t = Tail( args ) 
  t.create_dict()
  try:
    log = t.tail( open(file_name) )
    lines = t.grep( log ) 
    for each_line in lines:
      print each_line,

  except IOError, ioe:
    print "Unable to open " + file_name
  except KeyboardInterrupt, ke:
    print "Interrupted with Control-C"
    
if __name__ == '__main__': main()
