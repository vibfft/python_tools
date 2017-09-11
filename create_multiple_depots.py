#!/usr/bin/python

import os, sys, re, socket

from subprocess import Popen, PIPE

def get_depots(port):

  depot_name = socket.gethostname() 
  depot_cmd = ['p4','-p',port,'depots']
  depot_re = re.compile(r'^Depot\s+(\w+)\s+.*$')

  depots = []
  new_depot = ''

  try:
    (out,err) = Popen(depot_cmd, stdin=PIPE, stdout=PIPE).communicate()

    for each_line in out.split(os.linesep):
      m = depot_re.match(each_line)
      if m is not None:
        depots.append(m.group(1))

    new_depot = depot_name
    count = 0
    while(new_depot in depots):
      count += 1
      new_depot = depot_name + '_' + str(count)

    create_depot(new_depot, port)
        
  except Exception, e:
    print e

def create_depot(depot_name, port):

  depot_cmd = ['p4','-p',port,'depot','-i']
  depot_spec = 'Depot: ' + depot_name + '\n'
  depot_spec += 'Description: ' + depot_name + ' created\n'
  depot_spec += 'Type: local' + '\n'
  depot_spec += 'Map: ' + depot_name + '/...' 

  try:
    (out,err) = Popen(depot_cmd, stdin=PIPE, stdout=PIPE).communicate(input=depot_spec)
    print out
  except Exception, e:
    print e

def main():

  if len(sys.argv) != 2:
    print("{0} <port>\n".format(sys.argv[0]))
    sys.exit(1)

  port = sys.argv[1]
  get_depots(port)

if __name__ == '__main__':
  main()
