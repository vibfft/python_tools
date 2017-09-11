import unittest, os, sys, re, json
from subprocess import PIPE, Popen

class Test_EMS_Zookeeper(unittest.TestCase):

  def setUp(self):
    msg = " Run EMS "
    print
    print(msg.center(80,'#'))
    self.run_ems()

    msg = " Run ZK"
    print
    print(msg.center(80,'#'))
    self.run_zk()

  def run_ems(self):

    python_path = "/usr/bin/python"
    program_path = "ems_zookeeper.py"
    username = "wd-environments"
    password = "Bg7@+%EtgUSqCRKh"
    ems_cmd = [python_path, program_path, username, password]

    f_ems = open("ems.txt","w")
    try:
      (out,err) = Popen(ems_cmd,stdin=PIPE,stdout=PIPE).communicate()
      #print out 
      f_ems.write(out)

    except Exception, e:
      print e

    f_ems.close()

  def run_zk(self):
    sh_path = "/bin/sh"
    sh_program = "zk_reader.sh"
    argument = "/envTarget"
    zk_cmd = [sh_path, sh_program, argument]

    f_zk = open("zk.txt","w")
    try:
      (out,err) = Popen(zk_cmd,stdin=PIPE,stdout=PIPE).communicate()
      #print out 
      f_zk.write(out)

    except Exception, e:
      print e

    f_zk.close()

  def test_ems_validation(self):
    msg = " Running EMS test "
    print
    print(msg.center(80,'#'))

    ems_array = [
    '/databaseServers/name',
    '/databaseServers/port',
    '/databaseServers/user',
    '/databaseServers/lastUpdate',
    '/databaseServers/host',
    '/serviceGroups/name/stephen_group',
    '/serviceGroups/lastUpdate',
    '/serviceGroups/tenants/name',
    '/serviceGroups/tenants/lastUpdate',
    '/serviceGroups/tenants/customer/lastUpdate',
    '/serviceGroups/tenants/customer/name/DEF',
    '/serviceGroups/tenants/customer/lastUpdate',
    '/serviceGroups/tenants/customer/insightKey' ] 

    f_ems = open("ems.txt","r")
    lines = f_ems.readlines()
    for each_str in ems_array:
      for each_line in lines:
        if each_line.find( each_str ) != -1:
          print("STR => {0}: LN => {1}".format( each_str, each_line ) )
          self.assertTrue(True)

  def test_zk_validation(self):
    msg = " Running ZK test "
    print
    print(msg.center(80,'#'))

    zk_array = [
    'baseServer/x/properties',
    'databaseServer/x/properties/port',
    'databaseServer/x/properties/user',
    'databaseServer/x/properties/lastUpdate',
    'databaseServer/x/properties/host',
    'tenantGroup/stephen_group/properties',
    'tenantGroup/stephen_group/properties/lastUpdate',
    'tenantGroup/stephen_group/tenant/oms/properties',
    'tenantGroup/stephen_group/tenant/oms/properties/lastUpdate',
    'tenantGroup/stephen_group/tenant/oms/customer/properties/lastUpdate',
    'tenantGroup/stephen_group/tenant/oms/customer/DEF/properties',
    'tenantGroup/stephen_group/tenant/oms/customer/DEF/properties/lastUpdate',
    'tenantGroup/stephen_group/tenant/oms/customer/DEF/properties/insightKey' ]
    f_zk = open("zk.txt","r")
    lines = f_zk.readlines()
    for each_str in zk_array:
      for each_line in lines:
        if each_line.find( each_str ) != -1:
          print("STR => {0}: LN => {1}".format( each_str, each_line ) )
          self.assertTrue(True)
 
  def tearDown(self):

    msg = " Remove EMS and ZK files "
    print
    print(msg.center(80,'#'))
    os.remove( "zk.txt" )
    os.remove( "ems.txt" )

def main():
  unittest.main()

if __name__ == '__main__': main()
