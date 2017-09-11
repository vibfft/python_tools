#!/usr/bin/env python
#Author: Stephen Moon
#Date: 6/7/2014
#Summary:
#
#This program accepts two arugments from the command line.
#The first argument is the name of the input file and the second
#optional argument is used to generate a random number of unique
#input lines
#
#Typical output will have a list of unique lines sorted by their ocurrences
#in the input file.  Additionally, each line will be repeated by the random
#number generated based on the second optional argument.  If the optional 
#argument is not specified a default value of 2 is assumed.

import sys, os
from random import randrange
from pprint import pprint

class Unique_line_repeat(object):

  def __init__(self, file_name, repeat):

    self.filename = file_name
    self.repeat   = repeat
    self.str_repeat_dict = dict()

  def process_input(self):

    try: 
      f = open(self.filename,'r')
      for each_line in f.readlines():
        three_char_str = each_line.strip()  #strip the linefeed
        try:
          if self.str_repeat_dict[three_char_str]:  #if the key exists
            self.str_repeat_dict[three_char_str]['str_ct'] += 1 
        except KeyError:
        #if the key does not exist create a dictionary entry of
        #unique string count and repeat value returned by pseudo random
        #generator based on the input repeat value
                                                
          self.str_repeat_dict[three_char_str] = {'str_ct': 1, 
                                                  'rand_repeat': self.map_str_repeat(three_char_str)}
      f.close() #properly closing the descriptor

    except IOError as e:
      print e
    
    #dictionary items are sorted by "str_ct"   
    for each_str in sorted(self.str_repeat_dict.items(), key = lambda x: x[1]['str_ct']): 
      list_to_str = ','.join(each_str[1]['rand_repeat'])  #convert list into a string
      print('{0} {1}'.format(list_to_str, each_str[1]['str_ct']))

  def map_str_repeat(self, three_char_str):

    #repeat value returned by pseudo random generator based on the input repeat value 
    rand_repeat = randrange(1,int(self.repeat) + 1)
    comb_str_after_repeat = [] 
    [ comb_str_after_repeat.append(three_char_str) for i in range(rand_repeat) ]

    return comb_str_after_repeat

def main():

  if len(sys.argv) < 2 or len(sys.argv) > 3:
    print("Usage: {0} <full_path_of_text_file> [<repeat>]".format(sys.argv[0]))
    print("e.g.: \n\t{0} ~/test_input_file.txt 6".format(sys.argv[0]))
    print("\t{0} ~/test_input_file.txt\n".format(sys.argv[0]))
    sys.exit(1)

  file_name = sys.argv[1]  #input filename
  repeat    = 2            #default value for repeat range
  if len(sys.argv) == 2:
    pass
  else:
    repeat = sys.argv[2]   #only when the second argument is 
                           #specified, overwrite the default repeat range

  u_obj = Unique_line_repeat(file_name, repeat)
  u_obj.process_input()

if __name__ == '__main__':
  main()  
