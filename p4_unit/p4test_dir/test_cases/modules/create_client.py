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
#

import os, sys, re, socket
from subprocess import Popen, PIPE

class Client():
  
  def __init__(self, client_name, user_name, depot_name):
 
    self.clientDict = {}
    self.client_name = client_name
    self.depot_name = depot_name
    self.user_name = user_name

  def populateDict(self):

    client_cmd = ['p4', 'client', '-o']
    out = ""
    try:
      #print client_cmd
      (out,err) = Popen(client_cmd, stdout=PIPE, stderr=PIPE).communicate()
      #print out
    
    except Exception, e:
      print e 

    return out

  def makeDict(self,client_out):
    
    client        = re.compile('^Client:')
    owner         = re.compile('^Owner:')
    host          = re.compile('^Host:')
    description   = re.compile('^Description:')
    root          = re.compile('^Root:')
    options       = re.compile('^Options:')
    submitOptions = re.compile('^SubmitOptions:')
    lineEnd       = re.compile('^LineEnd:')
    view          = re.compile('^View:')

    viewOn = False
    viewList = []
    for each_line in client_out.split(os.linesep):

      if client.match(each_line):
        (k,v) = each_line.split(':')
        #print k.strip() + " => " + v.strip()
        self.clientDict[k.strip()] = v.strip()

      elif owner.match(each_line):
        (k,v) = each_line.split(':')
        #print k.strip() + " => " + v.strip()
        self.clientDict[k.strip()] = self.user_name

      elif host.match(each_line):
        (k,v) = each_line.split(':')
        #print k.strip() + " => " + v.strip()
        self.clientDict[k.strip()] = v.strip() 

      elif description.match(each_line):
        (k,v) = each_line.split(':')
        #print k.strip() + " => " + v.strip()
        self.clientDict[k.strip()] = ""

      elif root.match(each_line):
        (k,v) = each_line.split('\t')
        #print k.strip() + " => " + v.strip()
        self.clientDict[k.split(':')[0]] = v.strip()

      elif options.match(each_line):
        (k,v) = each_line.split(':')
        #print k.strip() + " => " + v.strip()
        self.clientDict[k.strip()] = v.strip()

      elif submitOptions.match(each_line):
        (k,v) = each_line.split(':')
        #print k.strip() + " => " + v.strip()
        self.clientDict[k.strip()] = v.strip()

      elif lineEnd.match(each_line):
        (k,v) = each_line.split(':')
        #print k.strip() + " => " + v.strip()
        self.clientDict[k.strip()] = v.strip()

      elif view.match(each_line):
        (k,v) = each_line.split(':')
        #print k.strip() + " => " + v.strip()
        self.clientDict[k.strip()] = viewList 
        viewOn = True

      elif viewOn and each_line:
        viewList.append(each_line)

  def displayDict(self):

    for k,v in self.clientDict.iteritems():
      print k, v

  def createNewClient(self, depot_name):

    client_reg = re.compile(r'^Client (\S+) saved\.$')

    client_spec = ""
    for k, v in sorted(self.clientDict.iteritems()):

      #you cannot concat a list with a string
      if k == 'View':
        client_spec += k + ':' + os.linesep
        #client_spec += '\t' + v[0].split(' ')[0] + ' ' + v[0].split(' ')[1] + os.linesep
        client_spec += '\t//' + depot_name + '/...'  + ' ' + v[0].split(' ')[1] + os.linesep

      else:
        client_spec += k + ':' + '\t' + v + os.linesep

    client_cmd = ['p4', 'client','-i']

    try:
      (client_out, client_err) = Popen(client_cmd,stdout=PIPE,stdin=PIPE).communicate(input=client_spec)

      m = client_reg.match(client_out)
      if m != None:
        print 'Client: ' + m.group(1) + ' created.'
        return m.group(1)
    except Exception, e:
      print e

    return 'Client not created' 

def create_client(client_name, user_name, depot_name='depot'):

  c = Client(client_name, user_name, depot_name)

  out = c.populateDict()
  c.makeDict(out)
  #c.displayDict()

  orig_client = c.clientDict['Root']
  created_client = ''
  try:
    new_client = client_name 
    
    if os.path.exists(new_client):
      pass
    else:
      os.mkdir(new_client)

    c.clientDict['Root'] = c.clientDict['Root'] + os.sep + new_client 
    c.clientDict['Client'] = new_client 
    c.clientDict['Description'] = 'Client ' + new_client + ' created by ' + user_name
    viewOne = c.clientDict.pop('View')
    viewOne = ' '.join([viewOne[0].split(' ')[0], '//' + new_client + '/...'])
    c.clientDict['View'] = [viewOne]

    created_client = c.createNewClient(depot_name)

    c.clientDict['Root'] = orig_client

  except Exception as e:
    print e

  return created_client
