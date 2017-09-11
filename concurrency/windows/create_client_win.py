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

import os, sys, re, socket, time
from subprocess import Popen, PIPE

class Client():
  
  def __init__(self, port_num, user_name):
 
    self.clientDict = {}
    self.USER_NAME = user_name
    self.CLIENT_NAME = int(time.time())
    if port_num.isdigit():
      self.P4PORT = 'localhost:' + str(port_num)
    else:
      self.P4PORT = str(port_num)

  def populateDict(self):

    client_cmd = ['p4', '-p', self.P4PORT, '-u', self.USER_NAME, '-c', 'c' + str(self.CLIENT_NAME), 'client', '-o']
    out = ""
    try:
      (out,err) = Popen(client_cmd, stdout=PIPE, stderr=PIPE).communicate()
    
    except Exception as e:
      print(e)

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
        (k,v) = each_line.split(':',1)
        self.clientDict[k.strip()] = v.strip()

      elif owner.match(each_line):
        (k,v) = each_line.split(':',1)
        self.clientDict[k.strip()] = self.USER_NAME

      elif host.match(each_line):
        (k,v) = each_line.split(':',1)
        self.clientDict[k.strip()] = v.strip() 

      elif description.match(each_line):
        (k,v) = each_line.split(':',1)
        self.clientDict[k.strip()] = ""

      elif root.match(each_line):
        (k,v) = each_line.split(':',1)
        self.clientDict[k.split(':')[0]] = v.strip()

      elif options.match(each_line):
        (k,v) = each_line.split(':',1)
        self.clientDict[k.strip()] = v.strip()

      elif submitOptions.match(each_line):
        (k,v) = each_line.split(':',1)
        self.clientDict[k.strip()] = v.strip()

      elif lineEnd.match(each_line):
        (k,v) = each_line.split(':',1)
        self.clientDict[k.strip()] = v.strip()

      elif view.match(each_line):
        (k,v) = each_line.split(':',1)
        self.clientDict[k.strip()] = viewList 
        viewOn = True

      elif viewOn and each_line:
        viewList.append(each_line)

  def displayDict(self):

    for k,v in self.clientDict.iteritems():
      print("Key: {0}, Value: {1}".format(k, v))

  def createNewClient(self, depot_name):

    client_reg = re.compile(r'^Client (\S+) saved\..*')

    client_spec = ""
    for k, v in sorted(self.clientDict.iteritems()):

      #you cannot concat a list with a string
      if k == 'View':
        client_spec += k + ':' + os.linesep
        client_spec += '\t//' + depot_name + '/...'  + ' ' + v[0].split(' ')[1] + os.linesep

      else:
        client_spec += k + ':' + '\t' + v + os.linesep

    client_cmd = ['p4', '-p', self.P4PORT, '-u', self.USER_NAME, '-c', 'c' + str(self.CLIENT_NAME), 'client','-i']

    try:
      (client_out, client_err) = Popen(client_cmd,stdout=PIPE,stdin=PIPE).communicate(input=client_spec)

      m = client_reg.match(client_out)
      if m != None:
        print("Client: {0} created.".format(m.group(1)))
        return m.group(1)
    except Exception as e:
      print(e)

    return 'Client not created' 

def create_client(port_num, client_count, user_name, depot_name):

  c = Client(port_num, user_name)

  out = c.populateDict()
  c.makeDict(out)
  #c.displayDict()

  if port_num.isdigit():
    pass
  else:
    port_num = port_num.split(':')[1]

  orig_client = c.clientDict['Root']
  created_client = ''
  try:
    new_client = depot_name + '_t' + str(int(port_num) + client_count) 
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
    print(e)

  return create_client
