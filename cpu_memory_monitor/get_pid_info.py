#!/usr/bin/env python
#Author: Stephen Moon
#Date: 10/3/2013
#Summary:  This program monitors the cpu and memory usage of
#a program.  It also monitors the threads and processes spawned 
#from the program executable.
 
import psutil, datetime, time, sys, os, logging, sqlite3

def get_pid(p_list, process, option):

  try:
    if option == 'pid':
      p_obj = psutil.Process(int(process))
      return (p_obj,process)

    else:
      for each_p in p_list:
        p_obj = psutil.Process(each_p)
        #print("{0}, {1}".format(each_p, p_obj.name))

        if option == 'name' and p_obj.name == process:
          return (p_obj, each_p)
        else:
	  print("{0} does not exist".format(process))
          sys.exit(1)
  
  except psutil.error.NoSuchProcess, nsp_error:
    print("Invalid PID or non-existing PID specified")
    sys.exit(1)

def create_table(process,option):

  try:
    conn = sqlite3.connect('_'.join([process,option]))
    cur  = conn.cursor()
    cur.execute("create table processes (name text, pid integer, cpu_percent real, memory_percent real, \
               num_threads integer, num_children integer, phys_avail_mem real, virt_avail_mem real)")
    conn.commit()

  except sqlite3.OperationalError as e:
    print(e)
    print("Remove the DB file {0} and rerun the program".format('_'.join([process,option])))
    sys.exit(1)
    

  return '_'.join([process,option])

def insert_values_2_table(table_name, proc_name, pid, cpu_percent, mem_percent,
    num_threads, num_children, phys_avail_mem, virt_avail_mem):

  try:
    conn = sqlite3.connect(table_name)
    cur  = conn.cursor()
    cur.execute("insert into processes values (?, ?, ?, ?, ?, ?, ?, ?)",(proc_name, pid, cpu_percent, mem_percent,
    num_threads, num_children, phys_avail_mem, virt_avail_mem))
    conn.commit()

  except sqlite3.OperationalError as e:
    print(e)
    sys.exit(1)

def process_info(p_obj, each_p):

  print("Username: {0} Name: {1} PID: {2}".format(p_obj.username,p_obj.name,str(each_p)))
  print("CPU Time: {0}".format(str(p_obj.get_cpu_times())))
  print("CPU Percent: {0}".format(str(p_obj.get_cpu_percent(interval=1.0))))
  print("Memory Percent: {0}".format(str(p_obj.get_memory_percent())))
  print("Memory Info: {0}".format(str(p_obj.get_memory_info())))
  #print("IO counters: " + str(p_obj.get_io_counters()))
  print("Number of context switches: {0}".format(str(p_obj.get_num_ctx_switches)))
  if sys.platform == 'win32':
    print("Number of Threads: {0}".format(str(p_obj.get_num_threads())))
    print("List of threads: {0}".format(str(p_obj.get_threads())))
  print(''.center(80,' '))

  #print("Number of File Descriptors: " + str(p_obj.get_num_fds()))
  #print("Open files: " + p_obj.get_open_files())
  #print("Connections: " + p_obj.get_connections())
  #print("Memory Map: " + str(p_obj.get_memory_maps()))
  #print("UserName: " + p_obj.username)
  #print(datetime.datetime.fromtimestamp(int(p_obj.create_time)).strftime('%Y-%m-%d %H:%M:%S'))

def write_debug_info(table_name, p_obj, each_p, debug):

  debug(''.center(80,'#'))
  debug("{0:>30} {1:<10} ".format("Process Name: ", p_obj.name))
  debug("{0:>30} {1:<10} ".format("PID: ",each_p))
  debug("{0:>30} {1:<10} ".format("CPU Time: ", p_obj.get_cpu_times()))
  debug("{0:>30} {1:<10} ".format("CPU Percent: ", p_obj.get_cpu_percent(interval=1.0)))
  debug("{0:>30} {1:<10} ".format("Memory Percent: ", p_obj.get_memory_percent()))
  debug("{0:>30} {1:<10} ".format("Memory Info: ", p_obj.get_memory_info()))
  debug("{0:>30} {1:<10} ".format("Memory Ext: ", p_obj.get_ext_memory_info()))
  #debug("{0:>30} {1:<10} ".format("IO counters: ", p_obj.get_io_counters()))

  debug("{0:>30} {1:<10} ".format("Number of context switches: ", p_obj.get_num_ctx_switches))
  if sys.platform == 'win32':
    debug("{0:>30} {1:<10} ".format("Number of Threads: ", p_obj.get_num_threads()))
    debug("{0:>30} {1:<10} ".format("List of threads: ", p_obj.get_threads()))
  debug(''.center(80,'#'))
  debug("{0:>30} {1:<10} MB".format("Available Physical Memory: ", psutil.avail_phymem()/1000000))
  debug("{0:>30} {1:<10} MB".format("Available Virtual Memory: ", psutil.avail_virtmem()/1000000))
  #debug("{0:>30} {1:<10} MB".format("Physical Memory Usage: ", psutil.phymem_usage()/1000000.0))
  #debug("{0:>30} {1:<10} MB".format("Virtual Memory Usage: ", psutil.virtmem_usage()/1000000))
  debug("{0:>30} {1:<10} MB".format("Total Virtual Memory: ", psutil.total_virtmem()/1000000))
  #debug("{0:>30} {1:<10} MB".format("Virtual Memory: ", psutil.virtual_memory()/1000000))
  debug("{0:>30} {1:<10} MB".format("Used Physical Memory: ", psutil.used_phymem()/1000000))
  debug("{0:>30} {1:<10} MB".format("Used Virtual Memory: ", psutil.used_virtmem()/1000000))
  
  insert_values_2_table(table_name, p_obj.name, each_p, p_obj.get_cpu_percent(), p_obj.get_memory_percent(), p_obj.get_num_threads(),
                        len(p_obj.get_children(recursive=True)), psutil.avail_phymem()/1000000, psutil.avail_virtmem()/1000000)

def logAutomation(logName):

   #Enable logging of the backup script
   logging.basicConfig(
		        level=logging.DEBUG,
		        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
		        datefmt='%m-%d %H:%M',
		        filename= logName + ".log", 
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

def main():


  if len(sys.argv) != 3:
    print("Usage: {0} <process_id> pid | <process_binary_name> name ".format(sys.argv[0]))
    sys.exit(1)

  logName = os.path.basename(sys.argv[0]).split('.')[0] + '_' + sys.argv[1] + '_' + sys.argv[2]

  if os.path.exists(logName + '.log'):
    os.remove(logName + '.log')

  (p4debug, p4error) = logAutomation(logName)

  process = sys.argv[1]
  option  = sys.argv[2]
  p_list = psutil.get_pid_list()
  (p_obj, each_p) = get_pid(p_list, process, option)

  table_name = create_table(process,option)
  while(True):
    process_info(p_obj, each_p)
    write_debug_info(table_name, p_obj, each_p, p4debug.debug)
    time.sleep(120)

if __name__ == '__main__':
  main()
