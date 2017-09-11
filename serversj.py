#!/usr/bin/env python

import os, sys, time
from subprocess import PIPE, Popen

def run_servers_j( port,user='super_user' ):

  cmd = [ 'p4','-p',str(port),'-u',user,'-Zroute','servers','-J' ]

  try:
    ( out,err ) = Popen( cmd, stdin=PIPE, stdout=PIPE ).communicate()

    if err is not None:
      print( "ERR: {0}".format( err ) )
    print( "{0}".format(out))

  except Exception as e:
    print( e )

def get_port( file_name ):

#structure of input file
#SERVER_ID           	PID       	PORT      
#broker              	11971     	42101     
#depot-master        	11748     	60539     
#depot-standby_1     	11868     	60856     
#depot-standby_2     	11888     	35443     
#workspace-server_1  	11908     	56589     
#workspace-server_2  	11938     	55909     
#workspace-server_3  	11963     	44722     

  f = open( file_name,'r' )
  port = ''
  for each_line in f.readlines():
    if each_line.find('broker') != -1:
      (server, pid, port) = each_line.split('\t')
      #print("SRV: {0}, PID: {1}, PORT: {2}".format(server, pid, port))
      break

  return port.strip()

def main():

  if len(sys.argv) != 2:
    print("{0} <dcs_setup.PID|dcs_setup2.PID,dcs_no_master.PID>".format(sys.argv[0]))
    sys.exit(1)

  filename = sys.argv[1]
  port = get_port( os.path.join(os.environ['HOME'], 'bin', filename.strip()) )

  while True:
    os.system('cls' if sys.platform == 'win32' else 'clear')
      
    run_servers_j( port )
    time.sleep(5)

if __name__ == '__main__':
  main()


