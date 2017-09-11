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

import os, sys, re, time
from subprocess import Popen, PIPE

class User():
  
  def __init__(self, port_num, user_name):
 
    self.userDict = {}
    self.USER_NAME = user_name
    self.CLIENT_NAME = int(time.time())
    if port_num.isdigit():
      self.P4PORT = 'localhost:' + str(port_num)
    else:
      self.P4PORT = str(port_num)

  def populateDict(self):

    user_cmd = ['p4', '-p', self.P4PORT, '-u', self.USER_NAME, '-c', 'c' + str(self.CLIENT_NAME), 'user', '-o']
    out = ""
    try:
      (out,err) = Popen(user_cmd, stdout=PIPE, stderr=PIPE).communicate()
    
    except Exception as e:
      print(e) 

    return out

  def makeDict(self,user_out):
    
    user  = re.compile('^User:')
    email = re.compile('^Email:')
    fname = re.compile('^FullName:')

    for each_line in user_out.split(os.linesep):

      if user.match(each_line):
        (k,v) = each_line.split(':',1)
        self.userDict[k.strip()] = v.strip()
      elif email.match(each_line):
        (k,v) = each_line.split(':',1)
        self.userDict[k.strip()] = v.strip()
      elif fname.match(each_line):
        (k,v) = each_line.split(':',1)
        self.userDict[k.strip()] = v.strip()

  def displayDict(self):

    for k,v in self.userDict.iteritems():
      print("Key: {0}, Value: {1}".format(k, v))

  def createNewUser(self):

    user_reg = re.compile(r'^User (\S+) saved\..*')
    user_spec = (os.linesep).join([':'.join([str(k),str(v)]) for k, v in self.userDict.iteritems()])
    user_cmd = ['p4','-p', self.P4PORT, '-u', self.USER_NAME, '-c', 'c' + str(self.CLIENT_NAME), 'user', '-f', '-i']

    try:
      (user_out, user_err) = Popen(user_cmd,stdout=PIPE,stdin=PIPE).communicate(input=user_spec)
      m = user_reg.match(user_out)
      if m != None:
        print("User: {0} created".format( m.group(1)))
        return  m.group(1)

    except Exception as e:
      print(e)

    return 'User not created' 

def create_user(port_num, user_count, user_name, depot_name):

  u = User(port_num, user_name)

  out = u.populateDict()
  u.makeDict(out)
  #u.displayDict()

  if port_num.isdigit():
    pass
  else:
    port_num = port_num.split(':')[1]

  try:
    new_user = depot_name + '_u' + str(int(port_num) + user_count)

    u.userDict['User'] = new_user 
    u.userDict['Email'] = new_user + '@' + new_user
    u.userDict['FullName'] = new_user 

    created_user = u.createNewUser()
     
  except Exception as e:
    print(e)

  return created_user
