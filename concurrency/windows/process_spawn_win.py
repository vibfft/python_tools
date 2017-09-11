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
#Author: Stephen Moon
#This program spawns processes using Python's multiprocessing module.
#You can't have more clients than the available commands because there is at least
#one client for each commands.  If there are more commands than the available
#clients, there will be more than one command running in each client.
# 
#So far, I have tried to implement this for the commands worked on for lockless reads.
#But, the list may get expanded to be comprehensive.
#
#By manually modifying the code in main, you can increase the number of files to be
#added as well as number of runs for each command.  Each command will be put in a loop
#so that it runs continuously.  Each process will have the client number and
# the command that it is associated with as well as the instance number and run number.
#If any one instance of a command finishes the specified number of runs, it will kill
#all processes running concurrently.
#
#CAUTION: If you have more than one writer, you need to run them in a separate client
#for now.  Otherwise, you will get "No files in default changelist" error message.
#If you have two writers, specify at least two clients and so on.

import os, sys, shutil, time, re, socket, sqlite3
import multiprocessing, logging, create_client_win, create_file_win, create_user_win 
from subprocess import PIPE, Popen

'''

p4 fstat (have and working tables peeked and processed early - all tables except hx/dx)
p4 filelog (lockless)
p4 diff lockless (some options are not)
p4 submit (rewritten into two-stage commit, also updates 'maxCommitChange' post change
p4 integ/merge/copy (copy uses buffered hx/dx)
p4 interchanges (streams/copy uses hx/dx)
p4 istat
p4 changes
p4 dirs (lockless)
p4 sync
p4 streams
p4 files/sizes/print (-a only)
p4 diff2
p4 cstat (partial)
p4 opened (partial)
p4 resolved
p4 have
p4 annotate
p4 depots
p4 fixes
p4 jobs (-e still read locks indexes)
p4 integed 
p4 verify
p4 describe

'''

class P4_Process(object):

  count = 0  #counts for commands with single parameter
  icount = 0 #counts for commands with two parameters
  scount = 0 #counts for commands which submit
  def __init__(self, port, depot_name, super_user, program_instance): #port string from the stdin argument

    self.super_cmds = ('verify','admin','archive','restore','obliterate','load','unload')
    self.no_param  = ('branches','clients','counters','depots','jobs','keys','labels','streams','users')
    self.one_param = ('annotate','branches','changes','clients','counters','cstat','depots','dirs',
                      'filelog','files','fixes','fstat','have','integrated','istat','jobs','keys',
                      'labels','opened','print','resolved','sizes','sync','verify','describe')
    self.two_param = ('diff','interchanges','diff2','populate')
    self.two_param_submit = ('integ','copy','merge')
    self.PREFIX = '//' + depot_name + '/' 
    self.DEPOT_NAME = depot_name
    self.SUPER_USER = super_user 
    self.P4 = 'p4'
    self.P4_Ztrack = '-Ztrack'
    self.P4PORT = port
    self.run_cmd = [self.P4, self.P4_Ztrack, '-p', self.P4PORT, '-c']
    self.cmds_dict = dict()
    self.program_instance = program_instance 

  def exit_message(self, process_name, cmd, count):

    msg = ''
    bool_writer = False
    if cmd in self.two_param_submit: 
      msg = "Last " + str(cmd) + ": Process " + str(count) + " Name: " + process_name 
      bool_writer = True
    elif cmd in self.one_param: 
      msg = "Last " + str(cmd) + ": Process " + str(count) + " Name: " + process_name 
    elif cmd in self.two_param: 
      msg = "Last " + str(cmd) + ": Process " + str(count) + " Name: " + process_name

    self.write_to_sqlite3(cmd, process_name, count, bool_writer)
    print(msg.center(80,' '))

  def write_to_sqlite3(self, cmd, process_name, count, bool_writer):

    process_type = 'writer' if bool_writer else 'reader'
    self.insert_values_to_table(process_name, cmd, count, process_type) 

  def insert_values_to_table(self, process_name, cmd, count, process_type):

    try:
      conn = sqlite3.connect(self.program_instance +'_DB')
      cur = conn.cursor()
      cur.execute("insert into processes values (?, ?, ?, ?)", (process_name, cmd, count, process_type))
      conn.commit()
      cur.close()
      conn.close()

    except sqlite3.OperationalError as e:
      print(e)

  def calculate_elapsed_time(self, e, start_time, sentinel):

    current_time = time.time()
    elapsed_time = int(current_time - start_time)
    if int(sentinel) == elapsed_time:   #passed sentinel is string
      msg = ''
      print(msg.center(80,'@'))
      msg = " Sentinel: " + sentinel + ", Elapsed: " + str(elapsed_time) + " " 
      print(msg.center(80,'@'))
      msg = ''
      print(msg.center(80,'@'))
      e.set()
      return True  #yes, it hit sentinel

    if (elapsed_time % 100) == 0:   #passed sentinel is string
     msg = ''
     print(msg.center(80,'@'))
     msg = " Sentinel: " + sentinel + ", Elapsed: " + str(elapsed_time) + " "
     print(msg.center(80,'@'))
     msg = ''
     print(msg.center(80,'@'))


    return False   #no, it needs to wait

  def p4process(self, e, start_time, sentinel, process_name, fq_port, port, cmd, mcount, dirname, client_number):

    src_path = self.PREFIX + dirname #//depot_<hostname>/qa_test
    dest_path = self.PREFIX + process_name #//depot_<hostname>/integ1_t11112

    client_used = self.DEPOT_NAME + '_t' + str(int(port) + client_number)
    user_used = self.DEPOT_NAME + '_u' + str(int(port) + client_number)

    if cmd in self.one_param:
      self.run_cmd.append(client_used)
      self.run_cmd.append('-u')
      self.run_cmd.append(user_used)
      self.run_cmd.append(cmd)

      if cmd in self.no_param:
        pass 
      elif cmd == 'dirs':
        self.run_cmd.append(self.PREFIX + '*')    #//depot_<hostname>/*
      elif cmd == 'have':
        create_file_win.sync_files('sync', fq_port, client_used, user_used, dirname)
        self.run_cmd.append(src_path + '/...')  #//depot_<hostname>/qa_test/...
      else:
        self.run_cmd.append(src_path + '/...')  #//depot_<hostname>/qa_test/...

      P4_Process.count = 0
      while(P4_Process.count < mcount):
     
        try:
          P4_Process.count += 1
          (out,err) = Popen(self.run_cmd,stdin=PIPE,stdout=PIPE).communicate()
          msg = cmd + " from " + self.DEPOT_NAME + " p4process: " + process_name + "_PROCESS " + str(P4_Process.count)
          print(msg.center(80,'.'))
          sys.stdout.flush()
          time.sleep(2)

          if e.is_set() or self.calculate_elapsed_time(e, start_time, sentinel):
            self.exit_message(self.DEPOT_NAME + '_' + process_name, cmd, P4_Process.count)
            sys.exit(1)

        except Exception as e:
          p4error.exception(e)
     
      e.set() 
      self.exit_message(process_name, cmd, P4_Process.count)

    elif cmd in self.two_param: 

      self.run_cmd.append(client_used)
      self.run_cmd.append('-u')
      self.run_cmd.append(user_used)
      if cmd == 'interchanges':
        self.run_cmd.append(cmd)
        self.run_cmd.append('-f')
      elif cmd == 'populate':
        self.run_cmd.append(cmd)

      P4_Process.icount = 0
      while(P4_Process.icount < mcount):

        P4_Process.icount += 1
        if cmd == 'interchanges':
          self.run_cmd.append(src_path + '/...')    #//depot_<hostname>/qa_test/... 
          self.run_cmd.append(self.PREFIX + 'integ...')  #//depot_<hostname>/qa_test0/...

        elif cmd == 'populate':
          self.run_cmd.append('-d')
          self.run_cmd.append('submitting_change of ' + process_name)
          self.run_cmd.append(src_path + '/...')                             #//depot_<hostname>/qa_test/... 
          self.run_cmd.append(dest_path + str(P4_Process.icount) + 'p/...')  #//depot_<hostname>/qa_test0p/... 

        try:
          #print("cmd: " + cmd + " run: ",self.run_cmd)
          (out,err) = Popen(self.run_cmd,stdin=PIPE,stdout=PIPE).communicate()
          msg = cmd + " from " + self.DEPOT_NAME + " p4process: " + process_name + "_PROCESS " + str(P4_Process.icount)
          print(msg.center(80,'.'))
          sys.stdout.flush()
          time.sleep(2)

          if e.is_set() or self.calculate_elapsed_time(e, start_time, sentinel):
            self.exit_message(self.DEPOT_NAME + '_' + process_name, cmd, P4_Process.icount)
            sys.exit(1)

        except Exception as e:
          p4error.exception(e)

        finally:

          if cmd == 'populate':
            self.run_cmd.remove(dest_path + str(P4_Process.icount) + 'p/...') #//depot_<hostanme>/qa_test0p/... 
            self.run_cmd.remove(src_path + '/...')                            #//depot_<hostname>/qa_test/... 
            self.run_cmd.remove('submitting_' + process_name)
            self.run_cmd.remove('-d')
          elif cmd == 'interchanges':
            self.run_cmd.remove(self.PREFIX + 'integ...') #//depot_<hostname>/qa_test0p/... 
            self.run_cmd.remove(src_path + '/...')   #//depot_<hostname>/qa_test/... 

      e.set()
      self.exit_message(self.DEPOT_NAME + '_' + process_name, cmd, P4_Process.icount)

    elif cmd in self.two_param_submit:
      create_file_win.sync_files('sync', fq_port, client_used, user_used, dirname, self.PREFIX)

      while(P4_Process.scount < mcount):
        P4_Process.scount += 1
        try:
          (integ_array, resolve_array, submit_array) = create_file_win.integ_files(fq_port, client_used, user_used, process_name, cmd, P4_Process.scount, dirname, self.PREFIX)
          msg = cmd + " from " + self.DEPOT_NAME + " p4process: " + process_name + "_PROCESS " + str(P4_Process.scount)
          print(msg.center(80,'#'))
          sys.stdout.flush()
         
          if e.is_set() or self.calculate_elapsed_time(e, start_time, sentinel):
            self.exit_message(self.DEPOT_NAME + '_' + process_name, cmd, P4_Process.scount)
            sys.exit(1)

        except Exception as err:
          p4error.exception(err) 

      e.set()
      self.exit_message(self.DEPOT_NAME + '_' + process_name, cmd, P4_Process.scount)

  def p4info(self, port, user_name):

    info_cmd = ['p4','-p',port, '-u', user_name, 'info']
    configure_cmd = ['p4','-p',port, '-u', user_name, 'configure','show']

    try:
      (info_out,info_err) = Popen(info_cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE).communicate()

    except Exception as e:
      print(e)

    try:
      (conf_out,conf_err) = Popen(configure_cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE).communicate()

    except Exception as e:
      print(e)

def pick_changes_delete(port_num, chg, user_name):

  describe_cmd = ['p4','-p',port_num, '-u', user_name, 'describe','-s',chg]
  submit = re.compile(r'^\s+submitting_change\s\w+\s(.+)$')
  try:

    (describe_out,describe_err) = Popen(describe_cmd,stdin=PIPE,stdout=PIPE).communicate()
    for each_line in describe_out.split(os.linesep):
      m = submit.match(each_line)
      if m != None:
        return (chg, m.group(1))
        
  except Exception as e:
    print(e)
  
  return (chg,'no_submit') 

def get_changes(port_num, user_name):

  changes = []
  submits = []
  port = str(port_num)
  chg_regex = re.compile(r'^Change (\d+) on')
  changes_cmd = ['p4','-p', port, '-u', user_name, 'changes']

  try:

    (changes_out,changes_err) = Popen(changes_cmd,stdin=PIPE,stdout=PIPE).communicate()
    for each_line in changes_out.split(os.linesep):

      m = chg_regex.match(each_line)
      if m != None:
        (each_change, each_submit) = pick_changes_delete(port, m.group(1), user_name)
        if each_submit != 'no_submit':
          changes.append(each_change) 
          submits.append(each_submit)

  except Exception as e:
    print(e)

  return (changes, submits)

def get_shelved_changes(port_num, user_name):

  changes = []
  submits = []
  port = str(port_num)
  chg_regex = re.compile(r'^Change (\d+) on')
  changes_cmd = ['p4','-p', port, '-u', user_name, 'changes', '-s', 'shelved']

  try:

    (changes_out,changes_err) = Popen(changes_cmd,stdin=PIPE,stdout=PIPE).communicate()
    for each_line in changes_out.split(os.linesep):

      m = chg_regex.match(each_line)
      if m != None:
        (each_change, each_submit) = pick_changes_delete(port, m.group(1), user_name)
        if each_submit != 'no_submit':
          changes.append(each_change) 
          submits.append(each_submit)

  except Exception as e:
    print(e)

  return (changes, submits)
  
def get_clients(port_num, user_name, depot_name):

  clients = []
  port = str(port_num)
  client = re.compile(r'^Client (' + depot_name + '_t\d+) .+$')
  clients_cmd = ['p4','-p', port, '-u', user_name, 'clients']

  try:

    (clients_out,clients_err) = Popen(clients_cmd,stdin=PIPE,stdout=PIPE).communicate()
    for each_line in clients_out.split(os.linesep):

      m = client.match(each_line)
      if m != None:
        clients.append(m.group(1)) 

  except Exception as e:
    print(e)

  return clients 

def delete_clients(port, user_name, depot_name):

  clients = get_clients(port, user_name, depot_name)
  client_cmd = ['p4','-p', port, '-u', user_name, 'client', '-d', '-f']
  for each_num in clients:
    client = each_num

    try:
      client_cmd.append(client)
      (client_out,client_err) = Popen(client_cmd, stdin=PIPE, stdout=PIPE).communicate()

      print("client_delete:",client_out)
      print("client_delete_error:",client_err)

      shutil.rmtree(client)

    except Exception as e:
      print(e)

    finally:
      client_cmd.remove(client)

def get_users(port_num, user_name, depot_name):

  users = []
  port = str(port_num)
  user = re.compile(r'^(' + depot_name + '_u\d+) .+$')
  users_cmd = ['p4','-p', port, '-u', user_name, 'users']

  try:

    (users_out,users_err) = Popen(users_cmd,stdin=PIPE,stdout=PIPE).communicate()
    for each_line in users_out.split(os.linesep):

      m = user.match(each_line)
      if m != None:
        users.append(m.group(1)) 

  except Exception as e:
    print(e)

  return users 

def delete_users(port, user_name, depot_name):

  users = get_users(port, user_name, depot_name)
  user_cmd = ['p4','-p', port, '-u', user_name, 'user', '-d', '-f']
  for each_num in users:
    user = each_num

    try:
      user_cmd.append(user)
      (user_out,user_err) = Popen(user_cmd, stdin=PIPE, stdout=PIPE).communicate()

      print("user_delete:",user_out)

    except Exception as e:
      print(e)

    finally:
      user_cmd.remove(user)

def delete_changes(port, user_name):

  deleted_changes = []
  chg_regex = re.compile(r'^Change (\d+) deleted.')
  (changes, submits) = get_changes(port, user_name)
  change_cmd = ['p4','-p', port, '-u', user_name, 'change', '-d', '-f']
  for each_change in changes:
    try:
      change_cmd.append(each_change)
      (change_out,change_err) = Popen(change_cmd,stdin=PIPE,stdout=PIPE).communicate()
      m = chg_regex.match(change_out)
      if m != None:
        deleted_changes.append(m.group(1))

    except Exception as e:
      print(e)

    finally:
      change_cmd.remove(each_change)
  
  print("Changes deleted: ",deleted_changes)
 
  return (deleted_changes, submits) 

def delete_shelved_changes(port, user_name):

  deleted_changes = []
  chg_regex = re.compile(r'^Shelved Change (\d+) deleted.')
  (changes, submits) = get_shelved_changes(port, user_name)
  change_cmd = ['p4','-p', port, '-u', user_name, 'shelve', '-df', '-c']
  for each_change in changes:
    try:
      change_cmd.append(each_change)
      (change_out,change_err) = Popen(change_cmd,stdin=PIPE,stdout=PIPE).communicate()
      m = chg_regex.match(change_out)
      if m != None:
        deleted_changes.append(m.group(1))

    except Exception as e:
      print(e)

    finally:
      change_cmd.remove(each_change)
  
  print("Changes deleted: ",deleted_changes)
 
  return (deleted_changes, submits) 

def obliterate(port, submits, dirname, depot_name, user_name):

  oblit_cmd = ['p4','-p', port, '-u', user_name, 'obliterate', '-y']
  for each_submit in submits:
    try:
      oblit_cmd.append('//' + depot_name + '/' + each_submit + "*/...")
      (out,err) = Popen(oblit_cmd, stdin=PIPE, stdout=PIPE).communicate()
      print("Obliterated: branch //" + depot_name  + '/' + each_submit + "*/...")
    except Exception as e:
      print(e)

    finally:
      oblit_cmd.remove('//' + depot_name + '/' + each_submit + "*/...")
  try:
    oblit_cmd.append('//' + depot_name + '/' + dirname + "/...")
    (out,err) = Popen(oblit_cmd, stdin=PIPE, stdout=PIPE).communicate()
    print("Obliterated: branch //" + depot_name + '/' + dirname + "/...")
  except Exception as e:
    print(e)

def p4_clean(port_num, dirname, depot_name, user_name):

  port = str(port_num)

  (changes, submits) = delete_shelved_changes(port, user_name)
  delete_clients(port, user_name, depot_name)
  (changes, submits) = delete_changes(port, user_name)
  obliterate(port, submits, dirname, depot_name, user_name)
  (changes, submits) = delete_changes(port, user_name)
  delete_users(port, user_name, depot_name)
  #delete_depot(port, depot_name, user_name)

def delete_depot(port, depot_name, user_name):

  depot_cmd = ['p4', '-p', port, '-u', user_name, 'depot', '-f', '-d', depot_name]

  try:
    (out,err) = Popen(depot_cmd, stdin=PIPE, stdout=PIPE).communicate()
    print("Deleted: Depot {0}".format(depot_name))
    print("Error in delete_cmd: ", err)

  except Exception as e:
    print(e)

def build_cmd_list(writer_names, reader_names):

  cmds_list = []
  for name, nums in writer_names.iteritems():
    for i in range(nums):
      cmds_list.append(name)
    print("WRITER: {0} Counts: {1}".format(name, str(nums)))
  for name, nums in reader_names.iteritems():
    for i in range(nums):
      cmds_list.append(name)
    print("READER: {0} Counts: {1}".format(name, str(nums)))

  return cmds_list

def get_depot(port, user_name):

  depot_name = socket.gethostname()
  depot_cmd = ['p4', '-p', port, '-u', user_name, 'depots']
  depot_re = re.compile(r'^Depot\s+(.+)\s[\d/]+')

  depots = []
  new_depot = ''

  try:
    (out,err) = Popen(depot_cmd, stdin=PIPE, stdout=PIPE).communicate()
    print(out)
    for each_line in out.split(os.linesep):
	  m = depot_re.match(each_line)
	  if m is not None:
	    depots.append(m.group(1))

    count = 0
    new_depot = depot_name + '_' + str(count) #this is needed because p4 creates a client 
                                              #which is the same name as hostname by default
    while(new_depot in depots):
      count += 1
      new_depot = depot_name + '_' + str(count)

    new_depot = create_depot(new_depot, port, user_name)
  
  except Exception, e:
    print(e)

  return new_depot


def create_depot(depot_name, port, user_name):

  depot_type = 'local'

  depot_cmd = ['p4', '-p', str(port), '-u', user_name, 'depot', '-i']

  depot_spec  = 'Depot: ' +  depot_name + '\n'
  depot_spec += 'Description: ' + depot_name + ' desc' + '\n'
  depot_spec += 'Type: ' + depot_type + '\n'
  depot_spec += 'Map: ' + depot_name + os.sep + '...'

  try:
    (out,err) = Popen(depot_cmd, stdin=PIPE, stdout=PIPE).communicate(input=depot_spec)
    print("STDOUT: {0}".format(out))
    print("STDERR: {0}".format(err))

  except Exception as e:
    print(e)

  return depot_name  

def create_table(program_name):

  try:
    conn = sqlite3.connect(program_name + '_DB')
    c = conn.cursor()
    c.execute('drop table if exists processes')
    c.execute("create table processes (process_name text, cmd text, process_count integer, type text)")
    conn.commit()
    c.close()
    conn.close()

  except sqlite3.OperationalError as e:
    print(e)

def read_table(cmds_dict, program_instance, p_type):

  try:
    conn = sqlite3.connect(program_instance + '_DB')
    c = conn.cursor()
    p_writer = ('writer')
    for row in c.execute("SELECT * FROM processes where type =?", (p_type,)): 
      cmd = row[1].encode('ascii','ignore')
      p_count = int(row[2])
      p_type = row[3].encode('ascii','ignore')
      try:
        if cmds_dict[cmd]: 
          cmds_dict[cmd]['p_count'] += p_count #summing up process counts 

      except KeyError:
        cmds_dict[cmd] = {
                          'p_type': p_type,
                          'p_count': p_count
                         }
    c.close()
    conn.close()

  except sqlite3.OperationalError as e:
    print e

  return cmds_dict

def report_summary(start_time, program_instance):


  cmds_dict = dict()
  cmds_dict = read_table(cmds_dict, program_instance, 'writer')
  tmp_dict = read_table(cmds_dict, program_instance, 'reader')

  cmds_dict.update(tmp_dict) #combine two dictionaries

  msg = ''
  print('\n')
  print(msg.center(80,'@'))
  msg = ' Report Summary '
  print(msg.center(80,'@'))
  msg = ''
  print(msg.center(80,'@'))
  
  writer_count = reader_count = 0 
  for cmd, val in sorted(cmds_dict.iteritems(), key = lambda x: x[1]['p_count']):
    print("{0:<10}\t{1:<5}\t{2:<5}".format(cmd, val['p_type'],val['p_count']))

    if val['p_type'] == 'writer':
      writer_count += val['p_count']
    elif val['p_type'] == 'reader':
      reader_count += val['p_count']

  msg = ''
  print(msg.center(80,'@'))
  print("Total of Readers: {0:<5} ".format(reader_count))
  print("Total of Writers: {0:<5} ".format(writer_count))
  print("Total of Readers and Writers: {0:<5} ".format(writer_count + reader_count))

  msg = ''
  print(msg.center(80,'@'))

  elapsed_time = time.time() - start_time
  print("Elapsed time: {0}".format(elapsed_time))

  msg = ''
  print(msg.center(80,'@'))

def main():

  if len(sys.argv) < 5 or len(sys.argv) > 6:
    print("Usage: {0} <port_number> <number of clients> <p4_super_user> <sentinel_seconds> [clean]".format(sys.argv[0]))
    sys.exit(1)

  port          = sys.argv[1]
  num_client    = sys.argv[2]
  p4_super_user = sys.argv[3] 
  sentinel      = sys.argv[4] 

  clean         = (sys.argv[5] if len(sys.argv) == 6 else "") 

  depot_name = get_depot(port, p4_super_user)
  dir_or_fname = 'qa_test'

  if len(sys.argv) == 6 and clean.strip() == 'clean':
    p4_clean(port, dir_or_fname, depot_name, p4_super_user)
    sys.exit(1)
  elif len(sys.argv) == 6 and clean.strip() != 'clean':
    print("Usage: {0} <port_number> <number of clients> <p4_super_user> <sentinel_seconds> [clean]".format(sys.argv[0]))
    sys.exit(1)

  #writer_names = {'copy':20,'integ':20} #'<cmd>:<writer_number>'
  writer_names = {'merge':10,'copy':10,'integ':15} #'<cmd>:<writer_number>'
  #reader_names = {}
  reader_names = {'filelog':5,'fstat':5,'interchanges':10,'diff':5,'changes':5,'obliterate':5,'diff2':5,'integed':10,'sync':10,'print':5} 

  cmds_list = build_cmd_list(writer_names, reader_names) 

  print(cmds_list)
  print("Number of commands: {0}".format(len(cmds_list)))
  if int(num_client) < 1 or len(cmds_list) < int(num_client):
    if not int(num_client):
      print("No client specified")
    else:
      print("Number of clients greater than the available commands")
    sys.exit(1)

  cmd = ''
  program_instance = os.path.basename(sys.argv[0]).split('.')[0] + '_' + port + '_' + num_client + '_' + sentinel
  create_table(program_instance)
  p_obj = P4_Process(port, depot_name, p4_super_user, program_instance)
  sys.stdout.flush()

  p_obj.p4info(port,p4_super_user)
  for each_item in range(int(num_client)):
    new_user = create_user_win.create_user(port, each_item, p4_super_user, depot_name)
    time.sleep(1.5)
    create_client_win.create_client(port, each_item, new_user, depot_name)

  #file_num = 20000
  integ_repeated = 4 

  fq_port = '' #fully qualified port
  if port.isdigit():
    fq_port = 'localhost:' + str(port)
  else:
    fq_port = port #perforce.com:1666
    port = port.split(':')[1] #1666

  #cmd, fq_port, client, user, path, dirname, integ_repeated, p4debug, p4error
  client  = depot_name + '_t' + str(port)
  user    = depot_name + '_u' + str(port)
  path    = depot_name + '_t' + str(port)
  create_file_win.fast_open_files('add', fq_port, depot_name, client, user, path, dir_or_fname, integ_repeated)

  file_num = 500 * (2 ** integ_repeated) 
  msg = " Done adding " + str(file_num) + " files. " 
  print(msg.center(80,'#'))

  jobs = []
  count = 1000000 
 
  #multiprocessing.log_to_stderr()
  #logger = multiprocessing.get_logger()
  #logger.setLevel(logging.INFO)

  e = multiprocessing.Event()
  seq = 0 
  elapsed_time = 0.0
  start_time = time.time()
  for cmd in cmds_list:
    seq += 1 

    client_number = seq % int(num_client)
    process_name = cmd + str(seq) + '_t' + str(int(port) + client_number)
    p = multiprocessing.Process(name=process_name, 
                                target=p_obj.p4process,args=(e, start_time, sentinel, process_name, fq_port, port, cmd, count, dir_or_fname, client_number))
    p.start()
    jobs.append(p)

  for each_p in jobs: 
    print('process_name from {0}: {1}'.format(depot_name , each_p))
    each_p.join()

  report_summary(start_time, program_instance)
    
if __name__ == '__main__':
  main()
