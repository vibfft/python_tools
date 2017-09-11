#!/usr/bin/env python
#
#Copyright (c) 2009, Perforce Software, Inc.  All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# 1.  Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
# 
# 2.  Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL PERFORCE SOFTWARE, INC. BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#*******************************************************************************
#
#Author: Stephen Moon
#Date: April 27, 2012 
#
#Summary: A program to test the performance of a Perforce Server on Linux 
#         
#         The program runs "changes -i, files, sync, flush, integrate, obliterate, etc."
#         against a server which does not have archived files.
#         
#         The program is not meant to replace the existing performance test run by
#         our performance lab, it is written to detect obvious memory leaks by
#         the lately released Perforce Server on Widnows.
#
#         1. The program first creates a client
#
#         2. Runs "p4 configure" to set the security level to 1 and disable 
#            memory retention of the SmartHeap.
#         3. After that, it does an initial stress test which verifies whether
#            there is any memory leak due to job042858
#         4. Once the stress is done, each command listed in the "cmds" list is
#            run against the server sequentially (i.e. in serial manner).
#         5. When the program is finished, it will have generated a log file
#            which shows the initial system information, each command ran and 
#            memory usage information after each run command run.
#
#Instruction to run the program:
#
# This program utilizes two libraries you may have not installed on your system:
#
#   Required package: P4Python
#
#   P4Python can be downloaded from ftp.perforce.com
#
# 1. Copy the program to an empty directory with the checkpoint (perftestchkpt.gz)
#    synced from //depot/dev/smoon/performance @ server.perforce.com:1666
#
# 2. Start the Perforce Server with the checkpoint.
#
# 3. Type "perf_test.py" at the command prompt for the required arguments for
#    the program to run the program against the server.
#
# 4. When the program is finished, you will find a log file which corresponds to
#    the port number of the Perforce server.
# 
# To do: Write a postprocessing script to compare the data (The test should be run
#        against two different servers.  i.e. A Known tested server and the latest
#        release.
#
#
#*******************************************************************************

import P4
from datetime import date
from subprocess import Popen,PIPE
import time, re, os, sys, optparse,logging

#Please note that this needs to be run against a perforce test server and you need
#to add appropriate perforce commands to cmds array.
cmds = [
['streams','//streams/...']]

def createClient(p4,p4port,p4user,p4debug,p4error):
  
  p4.client = p4user + "_ws"
  p4.port = p4port
  p4.user = p4user

  try:

    p4.connect()
    p4.password = "perforce1"
    p4.run_login()

    client = p4.run('client','-o')
    clientWS = p4user + "_ws"
    clientRoot = p4.cwd + os.sep + clientWS 

    if not (os.path.exists(clientRoot)):
      os.mkdir(clientWS)

    #for i in client[0]:
    #  print i

    client[0]['Client'] = clientWS 
    client[0]['Root'] = clientRoot
    client[0]['View'] = ["//DKGQ/... //" + clientWS + "/..."]
    client[0]['Options'].replace("normdir","rmdir")
    p4.save_client(client)

  except P4.P4Exception:
    for e in p4.errors:
      print e
      p4error.exception("{0}".format(e))

def stressTest(p4,p4port,p4user,p4debug,p4error):

  p4.client = p4user + "_ws"
  p4.port = p4port
  p4.user = p4user

  count = 3000
  
  #This test is to reproduce job42858
  try:

    for i in range(count):

      p4.connect()
      info = p4.run('info')
      p4.disconnect()

      if(not(i % count)):
        
        print "\np4 info ran " + str(count) + " times\n"
	print "Typical output of each run\n"
        
        for k,v in info[0].iteritems():
          print "{0:>30}: {1:<20}".format(k,v)
          p4debug.debug("{0:>30}: {1:<20}".format(k,v))

  except Exception, e:
    p4error.exception("{0}".format(e))

def runCommands(p4,p4port,p4user,p4debug,p4error):

  p4.client = p4user + "_ws"
  p4.port = p4port
  p4.user = p4user

  mem = re.compile('^Mem:\s+(\d+)\s+(\d+)\s+(\d+)\s+.*$')

  try:

    p4.connect()

    print "\nBaseline:"
    p4debug.debug("\nBaseline:")
    #memory usage
    runFreeMem(mem,p4debug)

    for eachList in cmds:

      cmd_str = ""
      for item in eachList:
        cmd_str = cmd_str + " " + item

      print "\n\nCmd: " + cmd_str
      p4debug.debug("\n\nCmd: {0}".format(cmd_str))

      t0 = time.clock()
      p4.run(eachList)

      print "{0:>30} {1:<20.3f}\n".format('Process Time (sec)',time.clock() - t0)
      p4debug.debug("{0:>30} {1:<20.3f}\n".format('Process Time (sec)',time.clock() - t0))
      runFreeMem(mem,p4debug)

    print "\n\nDone!\n"
    p4debug.debug("\n\nDone!\n")

  except Exception, e:
    p4error.exception("{0}".format(e))

  p4.disconnect()


def runFreeMem(mem,p4debug):

  (mem_out,mem_err) = Popen(['free','-m'],stdout=PIPE,stderr=PIPE,close_fds=True).communicate()
  for each_line in mem_out.split(os.linesep):
    m = mem.match(each_line)

    if mem.match(each_line):
      print "{0:>30} {1:<20} MB".format('Total Memory:', m.group(1))
      p4debug.debug("{0:>30} {1:<20} MB".format('Total Memory:', m.group(1)))
      print "{0:>30} {1:<20} MB".format('Used Memory:', m.group(2))
      p4debug.debug("{0:>30} {1:<20} MB".format('Used Memory:', m.group(2)))
      print "{0:>30} {1:<20} MB".format('Free Memory:', m.group(3))
      p4debug.debug("{0:>30} {1:<20} MB".format('Free Memory:', m.group(3)))
  
def summaryLog(logName):

  #Enable logging of the backup script
  logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename=logName + ".log",
                    filemode='w')
  # define a Handler which writes INFO messages or higher to the sys.stderr
  console = logging.StreamHandler()
  console.setLevel(logging.INFO)
  # set a format which is simpler for console use
  formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
  # tell the handler to use this format
  console.setFormatter(formatter)
  # add the handler to the root logger
  logging.getLogger('').addHandler(console)

  #define all the environmental variables
  p4debug = logging.getLogger('p4debug')
  p4error = logging.getLogger('p4error')

  return (p4debug,p4error)

def configureServer(p4,p4debug,p4error):

  try:

    memPool = ['configure','set','sys.memory.poolfree=1']
    memProc = ['configure','set','sys.memory.procfree=1']
    security = ['configure','set','security=1']

    info = p4.run('info')
    mPool = p4.run(memPool)
    mProc = p4.run(memProc)
    sec = p4.run(security)

    for k,v in info[0].items():
      print "{0:>30} {1:<10}".format(k + ":",v)
      p4debug.debug("{0:>30} {1:<10}".format(k + ":",v))

    for k,v in mPool[0].items():
      print "{0:>30} {1:<10}".format(k + ":",v)
      p4debug.debug("{0:>30} {1:<10}".format(k + ":",v))

    for k,v in mProc[0].items():
      print "{0:>30} {1:<10}".format(k + ":",v)
      p4debug.debug("{0:>30} {1:<10}".format(k + ":",v))

    for k,v in sec[0].items():
      print "{0:>30} {1:<10}".format(k + ":",v)
      p4debug.debug("{0:>30} {1:<10}".format(k + ":",v))
 
  except Exception, e:
    p4error.exception("{0}".format(e))

  p4.disconnect()

def cleanUp(p4,p4port,p4user,p4debug,p4error):

  delClient=[]
  try:

    p4.connect()

    delClient = p4.run(['client','-d',p4user + '_ws'])

  except Exception, e:
    p4error.exception("{0}".format(e))

  p4.disconnect()

  print "{0:>30}".format(delClient)
  p4debug.debug("{0:>30}".format(delClient))

def run_trust(p4port):

  trust_cmd = ['p4','-p',p4port,'trust','-f']

  trust_ans = Popen(trust_cmd, shell=False, stdin=PIPE, stdout=PIPE)
  trust_ans.stdin.write("yes\n")
  trust_ans.stdin.flush()
  while True:
    output = trust_ans.stdout.readline()
    print("%s" %output)
    if output == "":
      break
    
def main():

  parser = optparse.OptionParser(usage="%prog p4port user", version="%prog v0.1")
  #parser.add_option("-v","--verbose",action="store_true",dest="verbose",help="Print debug messages to stdout")
  (options,args) = parser.parse_args() #by default sys.argv[1:]

  if len(args) != 2:
    parser.error("Incorrect number of arguments");

  p4 = P4.P4()

  p4port = args[0]
  p4user = args[1]

  portArry = p4port.split(':')

  logName = ''
  if(len(portArry) == 3):
    logName = portArry[2]
    print("SSL Port")
    run_trust(p4port)

  elif(len(portArry) == 2):
    logName = portArry[1]
    print("HOST Port")

  else:
    logName = portArry[0]
    print("Port")
  
  logName = ''
  if(len(portArry) == 2):
    logName = portArry[1] 
  else:
    logName = portArry[0]

  (p4debug,p4error) = summaryLog(logName)
  #print "OS: " + os.name

  createClient(p4,p4port,p4user,p4debug,p4error)

  configureServer(p4,p4debug,p4error)
  #exit(1)

  stressTest(p4,p4port,p4user,p4debug,p4error)

  runCommands(p4,p4port,p4user,p4debug,p4error)

  cleanUp(p4,p4port,p4user,p4debug,p4error)

if __name__ == '__main__':
  main()
