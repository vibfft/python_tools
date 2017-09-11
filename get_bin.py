#!/usr/bin/env python
#Author: Stephen Moon
#$DateTime$
#Summary:  This is the program which syncs binaries
#          from your repositories.
#         
#          It might not work in your environment, but it may work with
#          some customization.
#

import sys, os, re, platform, shutil, stat, time
from subprocess import Popen, PIPE
from datetime import date

class P4_Binary(object):

  def __init__(self, release, change):

    locate_cmd = ''
    root_dir = ''
    if sys.platform == 'win32':
      locate_cmd = ['where','p4']
      root_dir = os.environ['userprofile']

    else:
      locate_cmd = ['which','p4']
      root_dir = os.environ['HOME']
   
    try: 
      #stripping line-feed from the string
      self.P4 = Popen(locate_cmd,stdin=PIPE,stdout=PIPE).communicate()[0].rstrip(os.linesep)

    except Exception, e:
      print e

    self.BIN = root_dir + os.sep + 'bin' + os.sep
    self.DATE = ''
    self.CHANGE = change
    self.P4PORT = '<your_host>:<port>'
    self.P4USER = 'perforce'
    self.P4CLIENT = release + '_' + sys.platform + '_ws' 
    self.PATH_PREFIX = self.BIN + 'p4_bin'
    self.PLATFORM = ''
    self.REL = release
    self.ROOT = ''
    self.P4_FILES = []

  def create_client(self):

    root   = re.compile('^Root:')
    host   = re.compile('^Host:')
    option = re.compile('(^Options:\s+.+)(normdir).*$')
    view   = re.compile('^View:') 
    vline  = re.compile('(^\s+\/\/depot\/\.\.\.)\s+.*$')

    client_cmd = [self.P4,'-p',self.P4PORT,'-u',self.P4USER,'client','-o', self.P4CLIENT]

    client_out = ''
    try:
      client_out = Popen(client_cmd, stdout=PIPE).communicate()[0] 

    except Exception, e:
      print e

    tmp_string = '' 

    view_on = False
    for each_line in client_out.split(os.linesep):

      if root.match(each_line):
        self.get_date()
        tmp_string += 'Root:\t' + self.ROOT + '\n'

      elif option.match(each_line):
        m = option.match(each_line) #need to put here because of group regex match
        tmp_string += m.group(1) + 'rmdir' + '\n' 

      elif host.match(each_line):
        print
        #print("{0}".format(each_line))

      elif view.match(each_line):
        view_on = True
        tmp_string += each_line + '\n' 

      elif view_on == True and vline.match(each_line):
        tmp_string += '\t//depot/... //' + self.P4CLIENT + '/...' + '\n' 

      else:
        tmp_string += each_line + '\n' 

    #write the modified spec to the server
    create_client = [self.P4,'-p',self.P4PORT,'-u',self.P4USER,'client','-i']

    try:
      (create_client_out,create_client_err) = Popen(create_client, stdin=PIPE, stdout=PIPE).communicate(input=tmp_string)

      print("{0} client successfully created for PORT: {1}".format(self.P4CLIENT,self.P4PORT))

    except Exception, e:
      print e

  def choose_platform(self):

    if sys.platform == 'win32' and platform.architecture()[0] == '32bit':
      self.platform = 'bin.ntx86'
    elif sys.platform == 'win32' and platform.architecture()[0] != '32bit':
      self.platform = 'bin.ntx64'

    elif sys.platform == 'darwin' and platform.architecture()[0] == '32bit':
      self.platform = 'bin.darwin90u'
    elif sys.platform == 'darwin' and platform.architecture()[0] != '32bit':
      self.platform = 'bin.darwin90x86_64'

    elif sys.platform == 'linux2' and platform.architecture()[0] == '32bit':
      self.platform = 'bin.linux26x86'
    elif sys.platform == 'linux2' and platform.architecture()[0] != '32bit':
      self.platform = 'bin.linux26x86_64'

    else:
      self.platform = 'freebsd60x86'

  def sync_files(self):

    sync_cmd = [self.P4, '-p', self.P4PORT, '-c', self.P4CLIENT, '-u', self.P4USER, 'sync', '-f']

    p4_files = []
    if sys.platform == 'win32':
      self.P4_FILES = ['p4.exe','p4d.exe','p4p.exe','p4broker.exe','p4zk.exe']

    else:
      self.P4_FILES = ['p4','p4d','p4d.debug','p4p','p4broker','p4zk','p4zk.debug']

    self.choose_platform() 
    cmd_path = '//depot' + '/' + self.REL + '/p4-bin/' + self.platform + '/' 

    print
    print("#".center(80,'#'))

    for p4_file in self.P4_FILES:

      if self.CHANGE == "HEAD":
        pass
      else:
        p4_file = p4_file + "@" + self.CHANGE

      sync_cmd.append(cmd_path + p4_file)
      try:
        #print sync_cmd
        sync_out = Popen(sync_cmd,stdin=PIPE,stdout=PIPE).communicate()[0]
        print("{0} successfully copied for {1}".format(p4_file,self.platform))
        
      except Exception, e:
        print e

      finally:
        sync_cmd.remove(cmd_path + p4_file)

    print("#".center(80,'#'))

  def get_date(self):

    d = date.today()

    self.DATE = str(d.year) + '_' + str(d.month) + '_' + str(d.day)

    path = self.PATH_PREFIX
    self.path_exists(self.PATH_PREFIX) #create p4_bin directory if not exist
    self.ROOT = self.PATH_PREFIX + os.sep + self.DATE
    self.path_exists(self.ROOT)        #create todays date directory if not exist

  def path_exists(self,path):

    if os.path.exists(path):
      print("{0} already exists".format(path))
   
    else:
      os.mkdir(path)

  def delete_files(self):

    path = self.BIN
    for each_file in self.P4_FILES:
      path += each_file
      os.remove(path)
      path = self.BIN

  def copy_binary(self):

    where_cmd = [self.P4,'-p',self.P4PORT,'-u',self.P4USER,'-c',self.P4CLIENT,'where']

    depot_path = ''
    for each_file in self.P4_FILES:
      try:
        depot_path = '//depot/' + self.REL + '/p4-bin/' + self.platform + '/' + each_file
        where_cmd.append(depot_path)
        #print where_cmd
        where_out = Popen(where_cmd,stdin=PIPE,stdout=PIPE).communicate()[0] 
        #print where_out.split(' ')[2]
        #self.delete_files()
        time.sleep(1)
        shutil.copyfile(where_out.split(' ')[2].rstrip(os.linesep), self.BIN + each_file)
        os.chmod(self.BIN + each_file, 0755)
     
      except Exception, e:
        print e

      finally:
        where_cmd.remove(depot_path)

  def delete_client(self):

    client_cmd = [self.P4,'-p',self.P4PORT,'-u',self.P4USER,'client','-d']

    try:
      client_cmd.append(self.P4CLIENT)
      print("{0}".format(client_cmd))
      client_out = Popen(client_cmd, stdin=PIPE,stdout=PIPE).communicate()[0]      
      print("Client {0} is successfully deleted".format(self.P4CLIENT))

    except Exception, e:
      print e

def main():

  if len(sys.argv) < 2 or len(sys.argv) > 3:
    print("Usage: {0} <release> [<change>]".format(sys.argv[0]))
    sys.exit(1)

  change = ""
  if len(sys.argv) == 3:
    change = sys.argv[2]
  else:
    change = "HEAD" 

  p = P4_Binary(sys.argv[1], change) 
  p.delete_client()
  p.create_client()
  p.sync_files()
  p.copy_binary()

if __name__  == '__main__':
  main()
