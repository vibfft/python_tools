#*******************************************************************************
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

import os, sys, re
from subprocess import Popen, PIPE

class Change():
  
  def __init__(self, port_num, client_name, user_name):
 
    self.changeDict = {}
    self.client_name = client_name
    self.user_name = user_name
    if port_num.isdigit():
      self.P4PORT = 'localhost:' + str(port_num)
    else:
      self.P4PORT = str(port_num)

  def populateDict(self):

    change_cmd = ['p4', '-p', self.P4PORT, '-c', self.client_name, '-u', self.user_name, 'change', '-o']
    out = ""
    try:
      (out,err) = Popen(change_cmd, stdout=PIPE, stderr=PIPE).communicate()
    
    except Exception as e:
      print(e) 

    return out

  def makeDict(self,change_out):
    
    change        = re.compile('^Change:')
    client	  = re.compile('^Client:')
    user	  = re.compile('^User:')
    status 	  = re.compile('^Status:')
    description   = re.compile('^Description:')

    viewOn = False
    viewList = []
    for each_line in change_out.split(os.linesep):

      if change.match(each_line):
        (k,v) = each_line.split(':',1)
        self.changeDict[k.strip()] = v.strip()

      elif client.match(each_line):
        (k,v) = each_line.split(':',1)
        self.changeDict[k.strip()] = v.strip()

      elif user.match(each_line):
        (k,v) = each_line.split(':',1)
        self.changeDict[k.strip()] = v.strip()

      elif status.match(each_line):
        (k,v) = each_line.split(':',1)
        #self.changeDict[k.strip()] = v.strip()

      elif description.match(each_line):
        (k,v) = each_line.split(':',1)
        self.changeDict[k.strip()] = ""

  def displayDict(self):

    for k,v in self.changeDict.iteritems():
      print("Key: {0}, Value: {1}".format(k, v))

  def createNewChange(self):

    chg_reg = re.compile(r'^Change (\d+) created\..*')
    change_spec = (os.linesep).join([':'.join([str(k),str(v)]) for k, v in self.changeDict.iteritems()]) 
    changein_cmd = ['p4', '-p', self.P4PORT, '-c', self.client_name, '-u', self.user_name, 'change','-i']

    try:
      (chg_out, chg_err) = Popen(changein_cmd,stdout=PIPE,stdin=PIPE).communicate(input=change_spec)
      m = chg_reg.match(chg_out)
      if m is not None:
        change_number = m.group(1)
        return change_number
    except Exception as e:
      print(e)

    return 'No change number created' 

def create_change(port_num, client_name, user_name, process_name):

  c = Change(port_num, client_name, user_name)

  out = c.populateDict()
  c.makeDict(out)
  #c.displayDict()

  change_number = 0
  if port_num.isdigit():
    pass
  else:
    port_num = port_num.split(':')[1]

  try:
    c.changeDict['Client'] = client_name 

    if process_name == '':
      c.changeDict['Description'] = 'submitting_change by ' + user_name
    else:
      c.changeDict['Description'] = 'submitting_change of ' + process_name

    change_number = c.createNewChange()

  except Exception as e:
    print(e)

  return str(change_number)
