#!/usr/bin/python
#Author: Stephen Moon
#$DateTime: 2014/09/22 15:44:22 $
#$Change: 10226 $
#$Revision: #37 $
#Summary:
#
#This program set up a DCS environment on a single machine.
#It does not create VMs, but it sets up depot-master, depot-standbys, 
#workspace-servers, workspace-router.
#
#If you were to invoke without any arguments, the following options
#are presented:
#
#smoon@ubuntu:~/tmp/workspace-server_3$ dcs_setup.py
#Usage: /home/smoon/bin/dcs_setup.py <number_of_standby> <number_of_ws_server> [clean]
#e.g. /home/smoon/bin/dcs_setup.py 3 3
#
#If you were to specify "python dcs_setup.py 2 3", it will set up:
#
# one depot-master
# two depot-standbys
# three workspace servers
# one workspace router
#
#If you were to put "dcs_setup.py" script in your bin directory and your bin directory
#is in the path, you will find "dcs_setup.PID" and "dcs_setup.log" created.
#
#The following is the typical look of "dcs_setup.PID":
#
#SERVER_ID	        PID	PORT
#broker	                9676	57082
#depot-master	        9443	38758
#depot-standby_1	9573	35500
#depot-standby_2	9593	44730
#workspace-server_1	9613	52748
#workspace-server_2	9642	41195
#workspace-server_3	9668	58432
#
#First column is the server_id of each server
#Second column is the PID of each server
#Third column is the port number of each server
#
#Please note that sometimes some sleep time is needed after restart of
#the depot-master and this is highly dependent upon how fast your machine
#is. 
#
#Requirements and dependencies:
#
#Zookeeper with "localhost:2181" address
#Python 2.7 or higher
#[Optional]: zkMonitor.py

import os, sys, re, socket, errno, logging, time, shutil, locale
from subprocess import PIPE, Popen

class Server(object):

  def __init__(self, standby, ws_server, encoding, p4debug, p4error):
    
    self.TMP = os.path.join(os.environ['HOME'],'tmp')

    self.encoding = encoding
    self.debug = p4debug.debug
    self.error = p4error.exception

    #self.peeking = peeking
    self.P4D = 'p4d'
    self.P4BROKER = 'p4broker'
    self.P4  = 'p4'
    self.dcs = {}

    self.bin_dir = os.path.join(os.environ['HOME'],'bin')

    self.num_standby = standby
    self.num_ws_server = ws_server

    self.MASTER    = 'depot-master'
    self.STANDBY   = 'depot-standby'
    self.WS_SERVER = 'workspace-server'
    self.ROUTER    = 'broker'
    self.ZOOKEEPER = 'localhost:2181'
    self.CLUSTER_NAME = '_'.join([os.path.basename(os.environ['HOME']),'cluster']) 

    self.MASTER_PORT = ''
    self.servers = {} 
    #self.service_users = {} 

    self.SUPER_USER = 'super_user'
    self.SERVICE_USER = 'dcs_user'
    self.SERVER_DEPOT_ROOT = os.path.join(self.TMP,'shared')
    self.MASTER_ROOT  = os.path.join(self.TMP,self.MASTER)
    self.STANDBY_ROOT = os.path.join(self.TMP,self.STANDBY)
    self.WS_SERVER_ROOT = os.path.join(self.TMP,self.WS_SERVER)
    self.ROUTER_ROOT = os.path.join(self.TMP,self.ROUTER)
    self.P4ZK_LOGFILE_PATH = os.path.join(self.TMP,'p4zk_logfile')
    #self.ZOOKEEPER_ROOT = os.path.join(self.TMP,self.ZOOKEEPER)

  def build_servers(self):

    servers = []

    servers.append(self.MASTER)
    self.server_map(self.MASTER,self.MASTER)
    for i in range(self.num_standby):
      servers.append(self.STANDBY)
      self.server_map(self.STANDBY,self.STANDBY + '_' + str(i + 1))
    for i in range(self.num_ws_server):
      servers.append(self.WS_SERVER)
      self.server_map(self.WS_SERVER,self.WS_SERVER + '_' + str(i + 1))

    return servers

  def build_map(self, dcs, server_list):

    s_count = ws_count = 0
    map_dict = dict()
    for each_server in server_list:
      if each_server == self.MASTER:
        if sys.version_info.major == 3: #iteritems() removed and items() is a dictionary in Python 3.  If you want Python 2.7 items(),
                                        #you need to do list(items())
          map_dict = { (lambda x,y: x + '#' + y)(self.CLUSTER_NAME,k):v for k, v in dcs[self.CLUSTER_NAME].items() } 
          tmp_dict = { (lambda x,y: x + '#' + y)(self.MASTER,k):v for k, v in dcs[self.MASTER].items() } 
        else:
          map_dict = { (lambda x,y: x + '#' + y)(self.CLUSTER_NAME,k):v for k, v in dcs[self.CLUSTER_NAME].iteritems() } 
          tmp_dict = { (lambda x,y: x + '#' + y)(self.MASTER,k):v for k, v in dcs[self.MASTER].iteritems() } 
        map_dict.update(tmp_dict)
      elif each_server == self.STANDBY:
        s_count += 1
        if sys.version_info.major == 3:
          tmp_dict = { (lambda x,y: x + '#' + y)(self.STANDBY + '_' + str(s_count),k):v for k, v in dcs['_'.join([each_server,str(s_count)])].items() } 
        else:
          tmp_dict = { (lambda x,y: x + '#' + y)(self.STANDBY + '_' + str(s_count),k):v for k, v in dcs['_'.join([each_server,str(s_count)])].iteritems() } 
        map_dict.update(tmp_dict)
      elif each_server == self.WS_SERVER:
        ws_count += 1
        if sys.version_info.major == 3:
          tmp_dict = { (lambda x,y: x + '#' + y)(self.WS_SERVER + '_' + str(ws_count),k):v for k, v in dcs['_'.join([each_server,str(ws_count)])].items() } 
        else:
          tmp_dict = { (lambda x,y: x + '#' + y)(self.WS_SERVER + '_' + str(ws_count),k):v for k, v in dcs['_'.join([each_server,str(ws_count)])].iteritems() } 
        map_dict.update(tmp_dict)

    if sys.version_info.major == 3:
      return [ (lambda x,y: x + '=' + y)(k,str(v)) for k, v in map_dict.items() ] 
    else:
      return [ (lambda x,y: x + '=' + y)(k,str(v)) for k, v in map_dict.iteritems() ] 
         
  def server_map(self, server_type, server_id):

    self.dcs[self.CLUSTER_NAME] = {
                   'monitor':1,
                   'P4TARGET':self.MASTER_PORT,
                   'zk.host.port.pairs':self.ZOOKEEPER,
                   'p4.utils.dir':self.bin_dir,
                   'rpl.journal.ack':2,
                   'rpl.journal.ack.min':1,
                   'db.jnlack.shared':0,
                   'serviceUser':'dcs_user',
                   'server.depot.root':self.SERVER_DEPOT_ROOT,
                  }

    if server_type == self.MASTER:
      self.dcs[self.MASTER] = {
                  'cluster':5,
                  'rpl':2,
                  'zk':5,
                  'cluster.id':self.CLUSTER_NAME,
                  'p4zk.log.file':os.path.join(self.P4ZK_LOGFILE_PATH,'.'.join([self.MASTER,'zklog'])),
                  'journalPrefix':os.path.join(self.TMP,server_id,server_id)
                 }

    if server_type == self.STANDBY:
      self.dcs[server_id] = {
                   'cluster':5,
                   'rpl':2,
                   'zk':5,
                   'db.replication':'readonly',
                   'lbr.replication':'shared',
                   'cluster.id':self.CLUSTER_NAME,
                   #'startup.1':'journalcopy --durable-only -i 0 -b 1',
                   #'startup.1':'journalcopy --non-acknowledging -i 0 -b 1',
                   'p4zk.log.file':os.path.join(self.P4ZK_LOGFILE_PATH,'.'.join([server_id,'zklog'])),
                   'journalPrefix':os.path.join(self.TMP,server_id,server_id),
                   'startup.1':'journalcopy -i 0 -b 1',
                   'startup.2':'pull -L -i 1 -b 1'
                  }

    if server_type == self.WS_SERVER:
      self.dcs[server_id] = {
                     'cluster':5,
                     'rpl':2,
                     'zk':5,
                     'db.replication':'readonly',
                     'lbr.replication':'shared',
                     'cluster.id':self.CLUSTER_NAME,
                     'p4zk.log.file':os.path.join(self.P4ZK_LOGFILE_PATH,'.'.join([server_id,'zklog'])),
                     'journalPrefix':os.path.join(self.TMP,server_id,server_id),
                     'startup.1':'pull -i 0 -b 1'
                    }

  def configure_map(self,server_type,server_id):

    server_list = self.build_servers()

    map_list = self.build_map(self.dcs, server_list)

    configure_cmd = [self.P4,'-p',self.MASTER_PORT,'-u',self.SUPER_USER,'configure','set'] 

    for each_conf in sorted(map_list):

      try:
        configure_cmd.append(each_conf)
        self.debug("{0}".format(configure_cmd))
        (conf_out, conf_err) = Popen(configure_cmd, stdin=PIPE, stdout=PIPE).communicate()

        conf = (conf_out.decode(self.encoding)).strip()
        print("{0}".format(conf))
        self.debug("{0}".format(conf))

      except Exception as e:
        self.error(e)

      finally:
        configure_cmd.remove(each_conf)
                    
  def run_process(self, p4d_cmd, port, server_type, server_root):
   
    pid = 0 
    try:
      p4d_cmd.append('-p')
      p4d_cmd.append('localhost:' + str(port))
      p4d_cmd.append('-r')
      p4d_cmd.append(server_root)
      p4d_cmd.append('-L')
      p4d_cmd.append(os.path.basename(server_root) + '.log')
      print('SERVER_CMD: {0}'.format(p4d_cmd))
      self.debug('SERVER_CMD: {0}'.format(p4d_cmd))
      pid = Popen(p4d_cmd, stdin=PIPE, stdout=PIPE).pid
      print('P4D_PID: {0}'.format(pid))
      print('SERVERID: {0}\n'.format(os.path.basename(server_root)))
      self.debug('P4D_PID: {0}'.format(pid))
      self.debug('SERVERID: {0}'.format(os.path.basename(server_root)))
      time.sleep(2)

    except Exception as e:
      self.error(e)

    return (os.path.basename(server_root), port, pid)

  def run_broker(self, port, broker_config, server_root):

    broker_cmd = [self.P4BROKER,'-v3','-c', os.path.join(self.ROUTER_ROOT,broker_config),'-d']
   
    pid = 0
    try:
      print("BROKER_CMD: {0}".format(broker_cmd))
      self.debug("BROKER_CMD: {0}".format(broker_cmd))
      pid = Popen(broker_cmd, stdin=PIPE, stdout=PIPE).pid
      print('BROKER_PID: {0}'.format(pid))
      print('BROKER_ID: {0}\n'.format(os.path.basename(server_root)))
      self.debug('BROKER_PID: {0}'.format(pid))
      self.debug('BROKER_ID: {0}'.format(os.path.basename(server_root)))

    except Exception as e:
      self.error(e)

    return (os.path.basename(self.ROUTER_ROOT), port, pid)

  def configure_broker(self, broker_config, port, router_root):

    f = open(os.path.join(self.ROUTER_ROOT,broker_config),'w')
 
    #reverse pid key with port value in the dictionary
    if sys.version_info.major == 3:
      port_serverid_pid = {v:k for k, v in list(self.servers.items())}
    else:
      port_serverid_pid = {v:k for k, v in self.servers.items()}

    #self.MASTER_PORT => localhost:<some_num>
    master_port = int(self.MASTER_PORT.split(':')[1]) 
    target_port = (port_serverid_pid[master_port]).split(':')[1]

    router_str  = 'target = ' + str(self.servers[os.path.basename(self.MASTER_ROOT) + ':' + str(target_port)]) + ';\n'
    router_str += 'listen = ' + str(port) + ';\n' 
    router_str += 'directory = ' + self.ROUTER_ROOT + ';\n'
    router_str += 'logfile = ' + os.path.basename(self.ROUTER_ROOT) + '.log;\n'
    router_str += 'debug-level = cluster=6' + ';\n'
    router_str += 'admin-name = "Perforce Admins";\n'
    router_str += 'admin-phone = 999/911;\n'
    router_str += 'admin-email = perforce-admins@example.com;\n'
    router_str += 'service-user = dcs_user;\n\n'
    router_str += 'router: router1\n'
    router_str += '{\n\tcluster.id = ' + self.CLUSTER_NAME + ';\n'
    router_str += '\tp4.utils.dir = ' + self.bin_dir + ';\n'
    router_str += '\tzk.host.port.pairs = ' + self.ZOOKEEPER + ';\n}\n'

    router_str += 'command: .*\n'
    router_str += '{\n\taction = redirect;\n'
    router_str += '\tuser = service_user;\n'
    router_str += '\tdestination target;\n}\n'

    router_str += 'command: configure\n'
    router_str += '{\n\taction = reject;\n'
    router_str += '\tmessage = "Not allowed for clusters - see SMT";\n'
    
    cluster_conf = '(cluster|jsplzk|p4zk|p4\.utils|rpl\.forward)[^=]*='
    router_str += '\targs = ' + cluster_conf + ';\n}\n'

    router_str += 'command: admin\n'
    router_str += '{\n\taction = reject;\n'
    router_str += '\tmessage = "Not allowed for clusters - see SMT";\n'
    router_str += '\targs = checkpoint|journal|stop|restart|dump|import;\n}\n'

    router_str += 'command: cluster\n'
    router_str += '{\n\taction = reject;\n'
    router_str += '\tmessage = "Not allowed for clusters - see SMT";\n}\n'

    router_str += 'command: cachepurge\n'
    router_str += '{\n\taction = reject;\n'
    router_str += '\tmessage = "Not allowed for clusters - see SMT";\n}\n'
   
    f.write(router_str)
    f.close()
 
  def p4d_process(self,server_type):

    if server_type == 'depot-master':

      port = self.get_avail_local_port()
      self.mkdir_p(self.MASTER_ROOT)

      p4d_cmd = [self.P4D]
      (server_id, port, pid) = self.run_process(p4d_cmd, port, server_type, self.MASTER_ROOT)
      self.servers[':'.join([server_id,str(pid)])] = port 
      p4d_cmd = []
      self.configure_server(server_type, server_id, port, pid)

    if server_type == 'broker':

      broker_config = 'router1.cfg'
      port = self.get_avail_local_port()
      self.mkdir_p(self.ROUTER_ROOT)

      self.configure_broker(broker_config, port, self.ROUTER_ROOT)
      (server_id, port, pid) = self.run_broker(port, broker_config, self.ROUTER_ROOT)
      self.servers[':'.join([server_id,str(pid)])] = port
      p4d_cmd = []

    bcount = count = 0
    if server_type == 'depot-standby':

      bcount = self.num_standby
      while(count < bcount):
        count += 1
        port = self.get_avail_local_port()
        server_path = '_'.join([self.STANDBY_ROOT,str(count)])
        self.mkdir_p(server_path)

        self.create_serverspec(server_type, os.path.basename(server_path), port)
        self.ckp_master(os.path.basename(server_path), self.MASTER_PORT)
        self.restore_ckp(server_path, port)

        p4d_cmd = [self.P4D]
        (server_id, port, pid) = self.run_process(p4d_cmd, port, server_type, server_path)
        self.servers[server_id + ':' + str(pid)] = port 
        p4d_cmd = []
        self.configure_server(server_type, server_id, port, pid)

    bcount = count = 0
    if server_type == 'workspace-server':

      bcount = self.num_ws_server
      while(count < bcount):
        count += 1
        port = self.get_avail_local_port()
        server_path = '_'.join([self.WS_SERVER_ROOT,str(count)])
        #server_path = '/home/smoon/tmp/workspace' 
        self.mkdir_p(server_path)

        self.create_serverspec(server_type, os.path.basename(server_path), port)
        self.ckp_master(os.path.basename(server_path), self.MASTER_PORT)
        self.restore_ckp(server_path, port)

        p4d_cmd = [self.P4D]
        (server_id, port, pid) = self.run_process(p4d_cmd, port, server_type, server_path)
        self.servers[':'.join([server_id,str(pid)])] = port 
        p4d_cmd = []
        self.configure_server(server_type, server_id, port, pid)

  def configure_server(self, server_type, server_id, port, pid):
   
    if server_type == 'depot-master':
      self.MASTER_PORT = ':'.join(['localhost',str(port)])
      self.configure_map(self.MASTER_PORT, server_id)
      self.create_serverid(server_type, server_id, self.MASTER_PORT)
      self.create_serverspec(server_type, server_id, self.MASTER_PORT)
      self.create_serviceuser(server_id)
      self.create_groupuser()
      self.create_protections()
      self.restart(os.path.basename(self.MASTER), self.MASTER_PORT)

    elif server_type == 'depot-standby':
      self.create_serverid(server_type, server_id, port)
      self.restart(server_id, port)
      self.restart(os.path.basename(self.MASTER), self.MASTER_PORT)

    elif server_type == 'workspace-server':
      self.create_serverid(server_type, server_id, port)
      self.restart(server_id, port)
      self.restart(os.path.basename(self.MASTER), self.MASTER_PORT)

  def create_shared_depot(self, depot_name):

    depot_cmd = [self.P4, '-p', str(self.MASTER_PORT), '-u', self.SUPER_USER, 'depot', '-i']

    depot_path = os.path.join(self.TMP,os.path.join('shared',depot_name))
    depot_spec  = 'Depot: ' + depot_name                   + '\n'
    depot_spec += 'Description: ' + depot_name             + '\n'
    depot_spec += 'Type: local '                           + '\n'
    depot_spec += 'Map: ' + os.path.join(depot_path,'...') + '\n'

    self.mkdir_p(depot_path)
    try:
      self.debug("DEPOT_SPEC CMD: {0} ".format(depot_cmd))
      (spec_out, spec_err) = Popen(depot_cmd, stdin=PIPE, stdout=PIPE).communicate(input=depot_spec.encode(self.encoding))
      
      spec = (spec_out.decode(self.encoding)).strip()
      print("DEPOT_SPEC: {0} ".format(spec))
      self.debug("DEPOT_SPEC: {0} ".format(spec))
 
      if spec_err is not None:
        specerr = (spec_err.decode(self.encoding)).strip()
        print("DEPOT_SPEC_ERR: {0} ".format(specerr))
        self.debug("DEPOT_SPEC_ERR: {0} ".format(specerr))

    except Exception as e:
      self.error(e)

  def create_serverid(self, server_type, server_id, port):

    id_cmd = []

    id_cmd = [self.P4, '-p', str(port), '-u', self.SUPER_USER, 'serverid', server_id]

    try:
      self.debug("SERVER_ID: {0}".format(id_cmd))
      print("SERVER_ID: {0}".format(id_cmd))
      (id_out, id_err) = Popen(id_cmd, stdin=PIPE, stdout=PIPE).communicate()

      ID = (id_out.decode(self.encoding)).strip()
      print("{0}".format(ID))
      self.debug("{0}".format(ID))

      if id_err is not None: 
        IDERR = id_err.decode(self.encoding)
        print("{0}".format(IDERR))
        self.debug("{0}".format(IDERR))

    except Exception as e:
      self.error(e)

  def create_serverspec(self, server_type, server_id, port):

    spec_cmd = [self.P4, '-p', str(self.MASTER_PORT),'-u', self.SUPER_USER, 'server', '-i']

    server_spec = 'ServerID:' + server_id + '\n'
    server_spec += 'Type: server' + '\n'
    server_spec += 'Name: ' + server_id + '\n'
    server_spec += 'Address: ' + str(port) + '\n'
    server_spec += 'Services: ' + server_type + '\n'
    server_spec += 'Description: ' + server_type + '\n'

    try:
      self.debug("SERVER SPEC CMD: {0}".format(spec_cmd))
      (spec_out, spec_err) = Popen(spec_cmd, stdin=PIPE, stdout=PIPE).communicate(input=server_spec.encode(self.encoding))
      
      spec = (spec_out.decode(self.encoding)).strip()
      print("\nSERVER_SPEC: {0}".format(spec))
      self.debug("SERVER_SPEC: {0}".format(spec))

      if spec_err is not None:
        specerr = (spec_err.decode(self.encoding)).strip()
        print("\nSERVER_SPEC ERROR: {0}".format(specerr))
        self.debug("SERVER_SPEC ERROR: {0}".format(specerr))

    except Exception as e:
      self.error(e)

    finally:
      spec_cmd.remove('-i')

    srv = re.compile('^ServerID:\s+(\S+).*$')
    svc = re.compile('^Services:\s+(\S+).*$')

    try:
      spec_cmd.append('-o')
      spec_cmd.append(server_id)
      self.debug("ServerSpec CMD: {0}".format(spec_cmd))
      (s_out, s_err) = Popen(spec_cmd, stdin=PIPE, stdout=PIPE).communicate()

      s = (s_out.decode(self.encoding)).strip()
      for each_line in s.split('\n'):
        m_srv = srv.match(each_line)
        m_svc = svc.match(each_line)

        if m_svc != None:
          print("SERVER_SPEC saved for Services: {0}".format(str(m_svc.group(1))))
          self.debug("SERVER_SPEC saved for Services: {0}".format(str(m_svc.group(1))))

        if m_srv != None:
          print("SERVER_SPEC saved for ServerID: {0}".format(str(m_srv.group(1))))
          self.debug("SERVER_SPEC saved for ServerID: {0}".format(str(m_srv.group(1))))

    except Exception as e:
      self.error(e)

  def create_serviceuser(self, server_id):
    
    user_cmd = [self.P4, '-p', str(self.MASTER_PORT), '-u', self.SUPER_USER, 'user', '-f', '-i']

    user_spec  = 'User: ' + server_id + '_svc'     + '\n'
    user_spec += 'Type: service'                   + '\n' 
    user_spec += 'Email: ' + server_id + '_svc'    + '\n'
    user_spec += 'Fullname: ' + server_id + '_svc' + '\n'

    try:
      self.debug("USER_SPEC CMD: {0} ".format(user_cmd))
      (spec_out, spec_err) = Popen(user_cmd, stdin=PIPE, stdout=PIPE).communicate(input=user_spec.encode(self.encoding))

      spec = (spec_out.decode(self.encoding)).strip()
      print("USER_SPEC: {0} ".format(spec))
      self.debug("USER_SPEC: {0} ".format(spec))

    except Exception as e:
      self.error(e)
    
    return '_'.join([server_id,'svc'])

  def create_groupuser(self):

    group_cmd = [self.P4, '-p', str(self.MASTER_PORT), '-u', self.SUPER_USER, 'group', '-i']

    group_spec  = 'Group: service_users'       + '\n'
    group_spec += 'Timeout: unlimited'         + '\n'
    group_spec += 'PasswordTimeout: unlimited' + '\n'
    group_spec += 'Subgroups: '                + '\n'
    group_spec += 'Owners: '                   + '\n'
    group_spec += 'Users: '                    + '\n'
    group_spec += '\t' + self.SERVICE_USER     + '\n'

    try:
      self.debug("GROUP SPEC CMD: {0} ".format(group_cmd))
      (spec_out, spec_err) = Popen(group_cmd, stdin=PIPE,stdout=PIPE).communicate(input=group_spec.encode(self.encoding))

      spec = (spec_out.decode(self.encoding)).strip()
      print("GROUP SPEC: {0} ".format(spec))
      self.debug("GROUP SPEC: {0} ".format(spec))

    except Exception as e:
      self.error(e)

  def create_protections(self):

    protections_cmd = [self.P4,'-p',str(self.MASTER_PORT),'-u',self.SUPER_USER,'protect','-i']

    protect_spec  = 'Protections:'                + '\n'
    protect_spec += '\twrite user * * //...'      + '\n'
    protect_spec += '\tsuper user ' + self.SUPER_USER + ' * //...'   + '\n'
    protect_spec += '\tsuper user ' + self.SERVICE_USER + ' * //...' + '\n'

    try:
      self.debug("Protect SPEC CMD: {0} ".format(protections_cmd))
      (spec_out, spec_err) = Popen(protections_cmd,stdin=PIPE,stdout=PIPE).communicate(input=protect_spec.encode(self.encoding))

      spec = (spec_out.decode(self.encoding)).strip()
      print("Protect SPEC: {0} ".format(spec))
      self.debug("Protect SPEC: {0} ".format(spec))

    except Exception as e:
      self.error(e)

  def ckp_master(self, server_id, port):

    ctr_out = 0

    server_root = os.path.join(self.TMP, server_id)
    #create a directory
    if not os.path.exists(server_root):
      os.mkdir(server_root)

    #take a checkpoint of the master
    ckp_cmd = [self.P4,'-p', str(self.MASTER_PORT), '-u', self.SUPER_USER, 'admin', 'checkpoint']
    try:
      self.debug("Checkpoint CMD: {0}".format(ckp_cmd))
      (ckp_out, ckp_err) = Popen(ckp_cmd,stdin=PIPE,stdout=PIPE).communicate()
      print("{0}".format("Checkpoint created"))
      self.debug("{0}".format("Checkpoint created"))

    except Exception as e:
      self.error(e)

    time.sleep(2)

  def restore_ckp(self, server_root, port):

    ctr = ''
    #figure out the journal counter number
    counter_cmd = [self.P4,'-p', str(self.MASTER_PORT), '-u', self.SUPER_USER, 'counter', 'journal']
    try:
      self.debug("Journal Counter CMD: {0} ".format(counter_cmd))
      (ctr_out, ctr_err) = Popen(counter_cmd,stdin=PIPE,stdout=PIPE).communicate()

      ctr = (ctr_out.decode(self.encoding)).strip()
      print("Journal Counter: {0} ".format(ctr))
      self.debug("Journal Counter: {0} ".format(ctr))
      
    except Exception as e:
      self.error(e)

    time.sleep(2)

    #do not get rid of the strip() for ctr_out.  ctr_out has line-ending at the end
    #restore from the master checkpoint
    ckp_file = '.'.join([self.MASTER_ROOT,'ckp',str(ctr)])
    print("CKP: {0}".format(ckp_file))
    path_join = os.path.join(self.MASTER_ROOT,ckp_file)
    print("CKP PATH: {0}".format(path_join))
    restore_cmd = [self.P4D,'-r', server_root, '-jr', os.path.join(self.MASTER_ROOT,'.'.join([os.path.basename(self.MASTER_ROOT),'ckp',str(ctr)]))]
    print(restore_cmd)
    try:
      self.debug(restore_cmd)
      (restore_out, restore_err) = Popen(restore_cmd,stdin=PIPE,stdout=PIPE).communicate()

      restore = (restore_out.decode(self.encoding)).strip()
      print("{0}".format(restore))
      self.debug(restore)

    except Exception as e:
      self.error(e)

  def restart(self, server_id, port):

    restart_cmd = [self.P4,'-p', str(port), '-u', self.SUPER_USER, 'admin', 'restart']
    try:
      self.debug("RESTART CMD: {0}".format(restart_cmd))
      (restart_out, restart_err) = Popen(restart_cmd,stdin=PIPE,stdout=PIPE).communicate()
      print("{0} at PORT {1} restarted.\n".format(server_id, str(port)))
      self.debug("{0} at PORT {1} restarted.".format(server_id, str(port)))

    except Exception as e:
      self.error(e)

    time.sleep(2)

  def get_avail_local_port(self):

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('',0))

    return s.getsockname()[1]

  def mkdir_p(self, path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

def print_args(*args):

  print("Type of input: {0}".format(type(args))) 
  print(args)
  print("\n")
  for i, each_arg in enumerate(args[0]):
    print("sys.argv #{0}: {1}".format(i, each_arg)) 
  print("\n")

def dcs_log(log_name):

  logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
    datefmt='%m-%d %H:%M',
    filename=log_name + '.log',
    filemode='w'
    )

  console = logging.StreamHandler()
  console.setLevel(logging.INFO)
  
  formatter=logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')

  console.setFormatter(formatter)

  logging.getLogger('').addHandler(console)

  p4debug = logging.getLogger('p4debug')
  p4error = logging.getLogger('p4error')

  return (p4debug,p4error)

def run_admin_stop(srv_name, port, pid):

  admin_cmd = ['p4','-u','super_user','-p',port,'admin','stop']

  try:
    (admin_out, admin_err) = Popen(admin_cmd, stdin=PIPE, stdout=PIPE).communicate()

    adminerr = (admin_err.decode(self.encoding)).strip()
    print("ADMIN_STOP against {0} @PORT {1} @PID {2}".format(srv_name, port, pid))
    print("ERR: {0}".format(adminerr))

  except Exception as e:
    print("{0}".format(e))


def clean_up(file_name):

  server_id = port = pid = ''

  #shutdown each server
  f = open(file_name)
  count = 0
  for each_line in f.readlines():
    count += 1
    if count > 1:
      (server_id, pid, port) = each_line.split('\t')
      run_admin_stop(server_id, port, pid)
  f.close() #properly close the file descriptor

  delete_tmp()

def delete_tmp():
  #delete the tmp directory
  try:
    shutil.rmtree(os.path.join(os.environ['HOME'],'tmp'), ignore_errors=False, onerror=shutil_handler)
   
  except OSError as e:
    print("SHUTIL ERR: {0}".format(e))


def shutil_handler(func, path, exc):
    excvalue = exc[1]

    if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
      os.chmod(path, stat.S_IRWXU| stat.S_IRWXG| stat.S_IRWXO) # 0777
      func(path)
    else:
      #shutil.rmtree(path, ignore_errors=False)
      raise

def error_message(args):

    print("Usage: {0} <number_of_standby> <number_of_ws_server> [clean]".format(args[0]))
    print("e.g. {0} 3 3".format(args[0]))

def save_server_info(srv_obj, prog_name):

  f = open(".".join([prog_name,'PID']),'w')
  f.write("{0:<20}\t{1:<10}\t{2:<10}\n".format('SERVER_ID','PID','PORT'))

  if sys.version_info.major == 3:
    for k, v in sorted(srv_obj.servers.items()):
      print("SERVER => PID:{0}, PORT:{1}".format(k,v))
      f.write("{0:<20}\t{1:<10}\t{2:<10}\n".format(k.split(':')[0],k.split(':')[1],v))
  else:
    for k, v in sorted(srv_obj.servers.iteritems()):
      print("SERVER => PID:{0}, PORT:{1}".format(k,v))
      f.write("{0:<20}\t{1:<10}\t{2:<10}\n".format(k.split(':')[0],k.split(':')[1],v))
  f.close()

def main():
 
  if len(sys.argv) < 3 or len(sys.argv) > 4:
    error_message(sys.argv)
    sys.exit(1)

  num_standby   = int(sys.argv[1])
  num_ws_server = int(sys.argv[2])
  prog_name = sys.argv[0].split('.')[0]

  delete_tmp()
  (p4debug, p4error) = dcs_log(prog_name)

  if len(sys.argv) == 4 and sys.argv[3] == 'clean':
    clean_up(".".join([prog_name,'PID']))
    sys.exit(1)
  elif len(sys.argv) == 4 and sys.argv[3] != 'clean':
    error_message(sys.argv)
    sys.exit(1)

  encoding = locale.getdefaultlocale()[1]
  srv_obj = Server(num_standby, num_ws_server, encoding, p4debug, p4error) 
  for each_type in ['depot-master','depot-standby','workspace-server','broker']:
    srv_obj.p4d_process(each_type)

  save_server_info(srv_obj, prog_name)

if __name__ == '__main__':
  main()
