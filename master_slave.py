#!/usr/bin/env python
#
#Copyright (c) 2014, Perforce Software, Inc.  All rights reserved.
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
#$DateTime: 2014/10/03 13:52:57 $
#Program Description:
#
#This program sets up commit/edge or standard/replica server environment
#Running "python master_slave.py" will show the following: 
#
#Invalid command specified
#Usage: /home/smoon/bin/master_slave.py <# of servers> <type of server> <standard/peeking> [<clean>]
#e.g.: /home/smoon/bin/master_slave.py 2 commit-edge standard 
#Type of Servers:
#
#        build-server
#        commit-edge
#        forwarding-replica
#        forwarding-standby
#        replica
#        standby
#
#Running "python master_slave.py 3 forwarding-replica standard" will set up three servers with db.peeking
#set to 2:
#
#i.e. one master with 2 read-only replicas
#
#This will create "port_numbers.txt" file which contain
#the pid, server name, port number of each server.
#
#In addition to the log file, it will generate a perl script which can recreate the particular 
#distributed setup that you have just created.  If you want the commit/edge, standard/replica,
#master/build, or master/forwarding-replica customized, modify the script for a particular task.
#Also, it is handy to have this to see what commands and inputs are needed to create a particular
#distributed setup.  The script file is prepended with "run_" to the log file name without
#the extension.
#
#"python master_slave.py 2 commit-edge standard clean" will kill the servers
#specified in "port_numbers.txt"
#
#If you want to restart, you need to remove the p4root directories
#which are at the same directory level as where this script is run
#
#P4ROOT directories are deleted automatically on non-Windows environment, but
# on Windows, you need to delete them manually.
#
#Requirement: 
# 
#Python 2.7 or higher

import os, sys, socket, time, shutil, re, logging, errno, stat, locale
from subprocess import Popen, PIPE
from pprint import pprint

class Server(object):

  def __init__(self, port_num, server_type, master, slave, peeking, encoding, p4debug, p4error):
    cwd = os.getcwd()
	
    self.encoding = encoding #this value is normally utf-8, but on Windows it can be different
                             #this is needed for binary file which returns bytes
                             #whenever you get output from Perforce command or you input a string
                             #it needs to be encoded
    self.debug = p4debug.debug
    self.error = p4error.exception	
    self.peeking = peeking
    self.P4D = 'p4d'
    self.P4 = 'p4'
    self.P4PORT = port_num
    self.SLAVE = slave
    self.MASTER = master 
    self.SERVICE_USER = 'service_user'
    self.SUPER_USER = 'super_user'
    self.SERVER_TYPE = (server_type.split(':')[0], server_type.split(':')[1])
    self.SERVER_BIN = 'p4d'
    self.SLAVE_ROOT = os.path.join(cwd, self.SLAVE)
    self.MASTER_ROOT = os.path.join(cwd, self.MASTER)
	
  def p4d_process(self, server_count, port, f):
  
    server_cmd = [self.P4D, '-p', port]
    server_cmd.append('-L')

    pid = 0	
    if server_count == 0:
    #this is the master server
      self.convert_to_perl('mkdir', ' '.join(['mkdir',self.MASTER]), '', f)
      if not os.path.exists(self.MASTER):
        os.mkdir(self.MASTER)
      server_cmd.append(self.MASTER + '.log')
      server_cmd.append('-r')
      server_cmd.append(self.MASTER_ROOT)
	  
    else:
      time.sleep(10)
      #this is a slave server
      #the root directory is created in ckp_restore method
      server_cmd.append(self.SLAVE + '_' + str(server_count) + '.log')
      server_cmd.append('-r')
      server_cmd.append(self.SLAVE + '_' + str(server_count))
	  
    try:
      self.debug("SERVER_CMD: {0}".format(server_cmd))
      pid = Popen(server_cmd, stdin=PIPE,stdout=PIPE).pid
      print("P4D_PID: {0}".format(pid))
      self.debug("P4D_PID: {0}".format(pid))
      self.convert_to_perl(server_cmd[0],' '.join(server_cmd), '', f)
	  
    except Exception as e:
      self.error(e) 
    
    return (pid, port)
	
  def create_serverid(self, server_count, port, f):
  
    id_cmd = []
    if server_count == 0:
      id_cmd = [self.P4,'-p', str(port),'-u',self.SUPER_USER,'serverid', self.MASTER]
    else:
      id_cmd = [self.P4,'-p', str(port),'-u',self.SUPER_USER,'serverid', self.SLAVE + '_' + str(server_count)]
    try:
      time.sleep(2)
      self.debug("SERVER_ID: {0}".format(id_cmd))
      self.convert_to_perl(id_cmd[0],' '.join(id_cmd), '', f)
      (id_out, id_err) = Popen(id_cmd, stdin=PIPE, stdout=PIPE).communicate()
      print("{0}".format(id_out.decode(self.encoding)))
      self.debug(id_out.decode(self.encoding))
	  
    except Exception as e:
      self.error(e) 
	  
  def create_serverspec(self, server_count, port, f):
  
    spec_cmd = [self.P4,'-p',str(self.P4PORT),'-u',self.SUPER_USER,'server','-i']
	
    server_id = ''
    if server_count == 0:
      server_id = self.MASTER
    else:
      server_id = self.SLAVE + '_' + str(server_count)
	  
    server_type = ''
    if server_count == 0:
      server_type = self.SERVER_TYPE[0] 
    else:
      server_type = self.SERVER_TYPE[1]

    server_spec  = 'ServerID: ' + server_id   + '\n'
    server_spec += 'Type: server'             + '\n'
    server_spec += 'Name: '     + server_id   + '\n'
    server_spec += 'Address: '  + port        + '\n'
    server_spec += 'Services: ' + server_type + '\n'
    server_spec += 'Description: ' + server_type + '\n'

    try:
      self.debug("SERVER SPEC CMD: {0}".format(spec_cmd))
      self.convert_to_perl(spec_cmd[0],' '.join(spec_cmd), server_spec, f)
      (spec_out, spec_err) = Popen(spec_cmd, stdin=PIPE,stdout=PIPE).communicate(input=server_spec.encode(self.encoding))
      print("\nSERVER SPEC: {0}".format(spec_out.decode(self.encoding)))
      self.debug("SERVER SPEC: {0}".format(spec_out.decode(self.encoding)))

    except Exception as e:
      self.error(e) 

    finally:
      spec_cmd.remove('-i')

    svr = re.compile('^ServerID:\s+(\S+).*$')
    svc = re.compile('^Services:\s+(\S+).*$')
    try:
      spec_cmd.append('-o')
      spec_cmd.append(server_id)
      self.debug("ServerSpec CMD: {0}".format(spec_cmd))
      self.convert_to_perl(spec_cmd[0],' '.join(spec_cmd), '', f)
      (s_out, s_err) = Popen(spec_cmd, stdin=PIPE, stdout=PIPE).communicate()

      for each_line in s_out.decode(self.encoding).split('\n'):
        m_svr = svr.match(each_line)
        m_svc = svc.match(each_line)
        if m_svc != None:
          print("SERVER SPEC saved for Services: {0}".format(str(m_svc.group(1))))
          self.debug("SERVER SPEC saved for Services: {0}".format(str(m_svc.group(1))))
        if m_svr != None:
          print("SERVER SPEC saved for ServerID: {0}".format(str(m_svr.group(1))))
          self.debug("SERVER SPEC saved for ServerID: {0}".format(str(m_svr.group(1))))

    except Exception as e:
      self.error(e)

  def create_serviceuser(self, f):
  
    user_cmd = [self.P4,'-p', str(self.P4PORT),'-u',self.SUPER_USER,'user','-f','-i']
	
    user_spec  = 'User: ' + self.SERVICE_USER + '\n'
    user_spec += 'Type: service'              + '\n'
    user_spec += 'Email: ' + self.SERVICE_USER + '\n'
    user_spec += 'Fullname: ' + self.SERVICE_USER + '\n' 
				
    try:
      self.debug("USER SPEC CMD: {0} ".format(user_cmd))
      self.convert_to_perl(user_cmd[0],' '.join(user_cmd), user_spec, f)
      (spec_out, spec_err) = Popen(user_cmd, stdin=PIPE,stdout=PIPE).communicate(input=user_spec.encode(self.encoding))
      print("USER SPEC: {0} ".format(spec_out.decode(self.encoding)))
      self.debug("USER SPEC: {0} ".format(spec_out.decode(self.encoding)))

    except Exception as e:
      self.error(e)
	  
  def create_groupuser(self, f):
  
    group_cmd = [self.P4,'-p', str(self.P4PORT),'-u',self.SUPER_USER,'group','-i']
	
    user_spec  = 'Group: service_users '      + '\n'
    user_spec += 'Timeout: unlimited'         + '\n'
    user_spec += 'PasswordTimeout: unlimited' + '\n'
    user_spec += 'Subgroups: '                + '\n'
    user_spec += 'Owners: '                   + '\n'
    user_spec += 'Users: '                    + '\n'
    user_spec += '\t' + self.SERVICE_USER     + '\n'
				
    try:
      self.debug("GROUP SPEC CMD: {0} ".format(group_cmd))
      self.convert_to_perl(group_cmd[0], ' '.join(group_cmd), user_spec, f)
      (spec_out, spec_err) = Popen(group_cmd, stdin=PIPE,stdout=PIPE).communicate(input=user_spec.encode(self.encoding))
      print("GROUP SPEC: {0} ".format(spec_out.decode(self.encoding)))
      self.debug("GROUP SPEC: {0} ".format(spec_out.decode(self.encoding)))

    except Exception as e:
      self.error(e)
	
  def create_protections(self, f):
  
    protections_cmd = [self.P4,'-p',str(self.P4PORT),'-u',self.SUPER_USER,'protect','-i']
	
    protect_spec  = 'Protections:'                + '\n'
    protect_spec += '\twrite user * * //...'      + '\n'
    protect_spec += '\tsuper user ' + self.SUPER_USER + ' * //...'   + '\n'
    protect_spec += '\tsuper user ' + self.SERVICE_USER + ' * //...' + '\n'
    
    try:
      self.debug("Protect SPEC CMD: {0} ".format(protections_cmd))
      self.convert_to_perl(protections_cmd[0], ' '.join(protections_cmd), protect_spec, f)
      (spec_out, spec_err) = Popen(protections_cmd,stdin=PIPE,stdout=PIPE).communicate(input=protect_spec.encode(self.encoding))
      print("Protect SPEC: {0} ".format(spec_out.decode(self.encoding)))
      self.debug("Protect SPEC: {0} ".format(spec_out.decode(self.encoding)))

    except Exception as e:
      self.error(e)
	  
  def server_configure(self, server_count, f):


    configure_cmd = [self.P4,'-p', str(self.P4PORT), '-u', self.SUPER_USER, 'configure', 'set']
    peeking = 2 if self.peeking == 'peeking' else 0

    if server_count == 0:
      for each_configurable in ('monitor=2','server=3',
                                'P4LOG=' + self.MASTER + '.log',
                                'serviceUser=' + self.SERVICE_USER,
                                'db.peeking=' + str(peeking)):

        each_setting = self.MASTER + '#' + each_configurable	
        configure_cmd.append(each_setting)

        try:
          self.debug("CONFIGURE CMD: {0}".format(configure_cmd))
          self.convert_to_perl(configure_cmd[0], ' '.join(configure_cmd), '', f)
          (setting_out,err) = Popen(configure_cmd, stdin=PIPE, stdout=PIPE).communicate()
          print("SETTING: {0}".format((setting_out.decode(self.encoding)).strip()))
          self.debug("SETTING: {0}".format((setting_out.decode(self.encoding)).strip()))
          sys.stdout.flush()

        except Exception as e:
          self.error(e)

        finally:
          configure_cmd.remove(each_setting)

    else:
      time.sleep(2)

      standby =     [ 'P4TARGET=localhost:' + str(self.P4PORT),
                      'rpl=4','time=1','lbr=3',
                      'P4LOG=' + self.SLAVE + '_' + str(server_count) + '.log',
                      'startup.1=journalcopy -i 0 -b 1',
                      'startup.2=pull -L -i 1 -b 1',
                      'db.replication=readonly',
                      'lbr.replication=readonly',
                      'serviceUser=' + self.SERVICE_USER,
                      'monitor=2','server=3',
                      'db.peeking=' + str(peeking) ]

      non_standby = [ 'P4TARGET=localhost:' + str(self.P4PORT),
                      'rpl=4','time=1','lbr=3',
                      'P4LOG=' + self.SLAVE + '_' + str(server_count) + '.log',
                      'startup.1=pull -i 1',
                      'startup.2=pull -u -i 1',
                      'startup.3=pull -u -i 1',
                      'db.replication=readonly',
                      'lbr.replication=readonly',
                      'serviceUser=' + self.SERVICE_USER,
                      'monitor=2','server=3',
                      'db.peeking=' + str(peeking) ]

      configurables = standby if self.SERVER_TYPE[1] in ['standby','forwarding-standby'] else non_standby 
      for each_configurable in (configurables):

        each_setting = self.SLAVE + '_' + str(server_count) + '#' + each_configurable	
        configure_cmd.append(each_setting)

        try:
          self.debug("CONFIGURE CMD: {0}".format(configure_cmd))
          self.convert_to_perl(configure_cmd[0], ' '.join(configure_cmd), '', f)
          (setting_out,err) = Popen(configure_cmd, stdin=PIPE, stdout=PIPE).communicate()
          print("SETTING: {0}".format((setting_out.decode(self.encoding)).strip()))
          self.debug("SETTING: {0}".format((setting_out.decode(self.encoding)).strip()))
          sys.stdout.flush()

        except Exception as e:
          self.error(e)

        finally:
          configure_cmd.remove(each_setting)

  def take_checkpoint(self, server_count, f):

    ctr_out = 0 

    #create a directory
    self.convert_to_perl('mkdir', ' '.join(['mkdir', self.SLAVE + '_' + str(server_count)]), '', f)
    if not os.path.exists(self.SLAVE + '_' + str(server_count)):
      os.mkdir(self.SLAVE + '_' + str(server_count))

    ckp_cmd = [self.P4,'-p', str(self.P4PORT), '-u', self.SUPER_USER, 'admin', 'checkpoint']
    try:
      self.debug("Checkpoint CMD: {0}".format(ckp_cmd))
      self.convert_to_perl(ckp_cmd[0], ' '.join(ckp_cmd), '', f)
      (ckp_out, ckp_err) = Popen(ckp_cmd,stdin=PIPE,stdout=PIPE).communicate()
      print("{0}".format("Checkpoint created"))
      self.debug("Checkpoint created")

    except Exception as e:
      self.error(e)

    time.sleep(5)

  def ckp_restore(self, server_count, f):

    counter_cmd = [self.P4,'-p', str(self.P4PORT), '-u', self.SUPER_USER, 'counter', 'journal']
    try:
      self.debug("Journal Counter CMD: {0} ".format(counter_cmd))
      self.convert_to_perl(counter_cmd[0], ' '.join(counter_cmd), '', f)
      (ctr_out, ctr_err) = Popen(counter_cmd,stdin=PIPE,stdout=PIPE).communicate()
      print("Journal Counter: {0} ".format(ctr_out.decode(self.encoding)))
      self.debug("Journal Counter: {0} ".format(ctr_out.decode(self.encoding)))

    except Exception as e:
      self.error(e)

    time.sleep(2)

    #do not get rid of the strip() for ctr_out.  ctr_out has line-ending at the end
    ctr = (ctr_out.decode(self.encoding)).strip()
    restore_cmd = [self.SERVER_BIN,'-r', self.SLAVE_ROOT + '_' + str(server_count), '-jr', self.MASTER_ROOT + os.sep + 'checkpoint.' + str(ctr)]
    try:
      self.debug(restore_cmd)
      self.convert_to_perl(restore_cmd[0], ' '.join(restore_cmd), '', f)
      (restore_out, restore_err) = Popen(restore_cmd,stdin=PIPE,stdout=PIPE).communicate()
      print("{0}".format(restore_out.decode(self.encoding)))
      self.debug(restore_out.decode(self.encoding))

    except Exception as e:
      self.error(e)


  def restart(self, server_count, port, f):

    restart_cmd = [self.P4,'-p', str(port), '-u', self.SUPER_USER, 'admin', 'restart']
    try:
      self.debug("RESTART CMD: {0}".format(restart_cmd))
      self.convert_to_perl(restart_cmd[0], ' '.join(restart_cmd), '', f)
      (restart_out, restart_err) = Popen(restart_cmd,stdin=PIPE,stdout=PIPE).communicate()
      slave_name = self.SLAVE + '_' + str(server_count)
      print("{0} at PORT {1} restarted.".format(slave_name, str(port)))
      self.debug("{0} at PORT {1} restarted.".format(slave_name, str(port)))

    except Exception as e:
      self.error(e)

  def check_p4d_binary(self, product):

    version = re.compile('^Rev\.\s(\S+)\/(\S+)\/(\S+)\/(\d+).*$')

    m = ""
    release_info = '\n' 
    codeline = ''
    try:

      p4_cmd = [product.lower(),'-V']

      self.debug(p4_cmd)
      p4_out = Popen(p4_cmd,stderr=PIPE,stdout=PIPE).communicate()[0]

      for each_line in p4_out.decode(self.encoding).split(os.linesep):
        m = version.match(each_line)
        if version.match(each_line):
          self.debug(" PLATFORM: " + m.group(2) + \
                     " CODELINE: " + m.group(3) + \
                     " RELEASE: "  + m.group(4))

          release_info += 'PLATFORM: ' + m.group(2) + '\n'
          release_info += 'CODELINE: ' + m.group(3) + '\n'
          release_info += 'RELEASE:  ' + m.group(4) + '\n'
          codeline = m.group(3)
        
    except Exception as e:
      self.error(e)

    rel_list = []
    release_num = [] 
    rel_list = codeline.split('.')
    for each_item in rel_list:

      try:
        if isinstance(int(each_item), int):
          self.debug("{0} is an integer".format(each_item))
          release_num.append(each_item)
          
      except ValueError as ve:
        self.debug("{0} is not an integer".format(each_item))
    return (release_info, ''.join(release_num)) 

  def convert_to_perl(self, cmd_bin, cmd_str, input_str, f):

    if sys.platform != 'win32' and cmd_bin == 'p4d':
      f.write('print "' + cmd_str + '\\n\\n";\n')
      perl_str = 'system("' + cmd_str + ' &");'
      f.write(perl_str)

    elif sys.platform == 'win32' and cmd_bin == 'p4d':
      new_str = cmd_str.replace('\\','\\\\') 
      #print("Windows Path: {0}".format(new_str))
      f.write('print "' + new_str + '\\n\\n";\n')
      perl_str = 'system(1,"' + new_str + '");'
      f.write(perl_str)

    elif input_str == '':
      config_obj = re.compile(r"^(p4\s.*\sconfigure\sset\s)(.*)$")
      m = config_obj.match(cmd_str)
      if m is not None:
        perl_str = '`'.join(['',m.group(1) + '"' + m.group(2) + '"', ';'])
      else:
        perl_str = '`'.join(['',cmd_str, ';'])
      f.write(perl_str)

    else:
      perl_str = '`'.join(['','echo "' + input_str + '" | ' + cmd_str, ';'])
      f.write(perl_str)

    f.write('\n\n')

    if cmd_bin != 'p4d' or cmd_bin != 'p4d.exe':
      cmd_obj = re.compile(r"^`(.*)`$")
      m = cmd_obj.match(cmd_str)
      if m is not None:
        f.write('print "' + m.group(1) + '\\n\\n";\n')

    if cmd_bin == 'p4d' or cmd_bin == 'p4d.exe':
      f.write('sleep 10;')
      f.write('\n')

def get_avail_local_port():

  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.bind(('',0))
  
  return s.getsockname()[1]

def append_portname(port):

  fd = open('port_numbers.txt','a')
  fd.write(str(port) + '\n')
  fd.close()
  
def start_server(server_count, port_num_file, server_type, master_name, slave_name, peeking, encoding, p4debug, p4error, f):

  fd = open(port_num_file, 'w')  #this over-writes the previous port_numbers file
  fd.close()

  print("SERVER_TYPE: {0}".format(server_type))
  port_num = get_avail_local_port()
  srv = Server(port_num, server_type, master_name, slave_name, peeking, encoding, p4debug, p4error)
  (release_info, release_num) = srv.check_p4d_binary('P4D')
  print("{0}".format(release_info))  
  if int(release_num) < 20121:
    print("You need a release version later than 2012.1")
    sys.exit(1)
  elif int(release_num) < 20132 and server_type.split(':')[0] == 'commit-server':
    print("Commit/Edge feature was introduced in 2013.2 release")
    print("Please specify server_type other than commit-edge")
    sys.exit(1)
  elif int(release_num) < 20142 and server_type.split(':')[1] in ['standby','forwarding-standby']:
    print("Standby server can be only created for a release version later than 2014.1")
    print("Please specify server type other than 'standby' or 'forwarding-standby'")
    sys.exit(1)
  elif int(release_num) < 20133 and peeking == 'peeking':
    print("Lockless read feature was introduced in 2013.3 release")
    print("Please specify 'standard' rather than 'peeking'")
    sys.exit(1)
  elif int(release_num) > 20141 and peeking == 'peeking':
    print("Lockless read feature is default for a release version later than 2014.1")
    print("Please specify 'standard' rather than 'peeking'")
    sys.exit(1)

  if int(release_num) > 20141:
    srv.peeking = 'peeking'

  pid = 0
  pid_dict = {}
  for i in range(int(server_count)):
    port = str(int(port_num) + i)
    #append_portname (port)
    if i == 0:
      (pid, port) = srv.p4d_process(i, port, f)
      srv.create_serverid(i, port, f)
      srv.create_serverspec(i, port, f)
      srv.create_serviceuser(f)
      srv.create_groupuser(f)
      srv.create_protections(f)
      srv.server_configure(i, f)
      pid_dict[pid] = server_type.split(':')[0] + '_' + str(i) + ':' + str(port)
    else:
      srv.create_serverspec(i, port, f)
      srv.server_configure(i, f)
      srv.take_checkpoint(i, f)
      srv.ckp_restore(i, f)
      (pid, port) = srv.p4d_process(i,port, f)
      srv.create_serverid(i, port, f)
      srv.restart(i, port, f)
      pid_dict[pid] = server_type.split(':')[1] + '_' + str(i) + ":" + str(port)

    append_portname(str(pid) + ':' + pid_dict[pid])

  return(pid_dict)

def delete_p4root(count, master_name, slave_name):

  for i in range(count):

    try:
      if i == 0:
        shutil.rmtree(master_name, ignore_errors=False, onerror=shutil_handler)
        print("{0} P4ROOT deleted".format(master_name))
      else:
        shutil.rmtree(slave_name + '_' + str(i), ignore_errors=False, onerror=shutil_handler)
        print("{0} P4ROOT deleted".format(slave_name + '_' + str(i)))
      time.sleep(2)
    except OSError as e:
      print("SHUTIL ERROR: {0}".format(e))

def shutil_handler(func, path, exc):
  excvalue = exc[1]
  if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
      os.chmod(path, stat.S_IRWXU| stat.S_IRWXG| stat.S_IRWXO) # 0777
      func(path)
  else:
      #shutil.rmtree(path, ignore_errors=False)
      raise
 
def clean(master_name, slave_name):

  fd = open('port_numbers.txt','r')

  count = 0
  for each_line in fd.readlines():
    count += 1
    port = each_line.split(':')[2]
    srv_name = each_line.split(':')[1]
    run_admin_stop(srv_name, port.rstrip())

  #Python 2.7 returns 'linux2' whereas Python 3.x returns 'linux'
  if sys.platform == 'darwin' or sys.platform == 'linux2' or sys.platform == 'linux':
    delete_p4root(count, master_name, slave_name)

def run_admin_stop(srv_name, port):

  admin_cmd = ['p4','-u','super_user','-p',port,'admin','stop']

  try:
    #print("ADMIN STOP CMD: {0}".format(admin_cmd))
    (admin_out, admin_err) = Popen(admin_cmd, stdin=PIPE, stdout=PIPE).communicate()
    print("ADMIN_STOP against {0} @PORT {1}".format(srv_name, port))

  except Exception as e:
    print("{0}".format(e))
    
def get_avail_local_port():

  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.bind(('',0))
  
  return s.getsockname()[1]

def exit_message(args, server_dict):
  print("Invalid command specified")
  print("Usage: {0} <# of servers> <type of server> <standard/peeking> [<clean>]".format(args[0]))
  print("e.g.: {0} 2 commit-edge standard".format(args[0]))
  print("Type of Servers:")
  for k in sorted(server_dict.keys()):
    print("\t{0}".format(k))

def server_validation(server_dict, server_type):

  if sys.version_info.major == 3:
    for k, v in server_dict.items():
      if server_type.strip() == k:
        return server_dict[k]
  else:
    for k, v in server_dict.iteritems():
      if server_type.strip() == k:
        return server_dict[k]
  return 'Invalid_Type' 

def log_automation(log_name):

   #Enable logging of the backup script
   logging.basicConfig(
                        level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename= log_name + ".log",
                        filemode='w'
                      )

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

def server_map(dict_name):

  if dict_name == 'server_dict':

    server_dict = {
                 'commit-edge':'commit-server:edge-server',
                 'replica':'standard:replica',
                 'forwarding-replica':'standard:forwarding-replica',
                 'standby':'standard:standby',
                 'forwarding-standby':'standard:forwarding-standby',
                 'build-server':'standard:build-server'
                }
    return server_dict

  elif dict_name == 'master_dict':

    master_dict = {
                 'commit-edge':'COMMIT',
                 'replica':'MASTER',
                 'standby':'MASTER',
                 'forwarding-standby':'MASTER',
                 'forwarding-replica':'MASTER',
                 'build-server':'MASTER'
                }

    return master_dict

  elif dict_name == 'slave_dict':

    slave_dict = {
                 'commit-edge':'EDGE',
                 'replica':'RPL',
                 'standby':'STANDBY',
                 'forwarding-standby':'F_STANDBY',
                 'forwarding-replica':'FORWARD',
                 'build-server':'BUILD'
                }

    return slave_dict

def main():

  if len(sys.argv) < 4 or len(sys.argv) > 5:
    exit_message(sys.argv, server_map('server_dict'))
    sys.exit(1)

  server_num  = sys.argv[1]
  server_type = sys.argv[2]
  peeking = sys.argv[3]
  encoding = locale.getdefaultlocale()[1]

  if len(sys.argv) == 4:
    if server_validation(server_map('server_dict'), server_type) == 'Invalid_Type':
      exit_message(sys.argv, server_map('server_dict'))
      sys.exit(1)

    if peeking == 'peeking' or peeking == 'standard':
      pass
    else:
      print("Please choose 'peeking' or 'standard'")
      sys.exit(1)
     
  elif len(sys.argv) == 5:
    if server_validation(server_map('server_dict'), server_type) == 'Invalid_Type':
      exit_message(sys.argv, server_map('server_dict'))
      sys.exit(1)
    clean(server_map('master_dict')[server_type], server_map('slave_dict')[server_type])
    sys.exit(1)

  log_name = '_'.join([os.path.basename(sys.argv[0]).split('.')[0],sys.argv[1],sys.argv[2],sys.argv[3]])
  run_script = "run_" + log_name

  if os.path.exists(log_name + '.log'):
    os.remove(log_name + '.log')

  (p4debug, p4error) = log_automation(log_name)

  port_num_file = 'port_numbers.txt'

  f = open(run_script,'w')
  f.write('#/usr/bin/env perl')
  f.write('\n')
  pid_dict = start_server(server_num, port_num_file, server_map('server_dict')[server_type], 
                          server_map('master_dict')[server_type], server_map('slave_dict')[server_type], 
                          peeking, encoding, p4debug, p4error, f)

  if sys.version_info.major == 3:
    for k, v in sorted(pid_dict.items()):
      print("PID: {0}, SERVER NAME: {1} PORT: {2}".format(k, v.split(':')[0], v.split(':')[1]))
      f.write("# PID: {0}, SERVER NAME: {1} PORT: {2}\n".format(k, v.split(':')[0], v.split(':')[1]))
 
  else:
    for k, v in sorted(pid_dict.iteritems()):
      print("PID: {0}, SERVER NAME: {1} PORT: {2}".format(k, v.split(':')[0], v.split(':')[1]))
      f.write("# PID: {0}, SERVER NAME: {1} PORT: {2}\n".format(k, v.split(':')[0], v.split(':')[1]))

  f.close()

if __name__ == '__main__':
  main()
