import os, sys, re
from subprocess import Popen, PIPE
from create_user import create_user
from create_change import create_change
from create_client import create_client
from create_file import create_files

class P4_BASE(object):

  def __init__(self):
    self.P4USER = '' 
    self.P4CLIENT = '' 

  def run(self, *args):

    arg_array = []
    arg_array.append('p4')
    arg_array.append('-u')
    arg_array.append(self.P4USER)
    arg_array.append('-c')
    arg_array.append(self.P4CLIENT)
    for each_arg in args:
      arg_array.append(each_arg)

    cmd_out = '' 
    cmd_err = ''
    try:
      print arg_array
      (cmd_out,cmd_err) = Popen(arg_array, stdin=PIPE, stdout=PIPE).communicate()
      print cmd_out
      #print(''.center(80,'='))
    
    except Exception, e:
      print e

    return (cmd_out, cmd_err)

  def create_files(self, filename):
    create_files(filename)

  def create_client(self, client_name, user_name):
    return create_client(client_name, user_name)

  def create_user(self, user_name):
    return create_user(user_name)

  def set_user(self, user_name):
    self.P4USER = user_name

  def get_user(self):
    return self.P4USER
  
  def get_client(self):
    return self.P4CLIENT

  def set_client(self,client_name):
    self.P4CLIENT= client_name

def P4():

  p4 = P4_BASE()

  return p4
