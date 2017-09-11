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

import os, sys, copy, time, re, create_change, socket
from subprocess import PIPE, Popen

def create_files(filename,p4debug,p4error):

  if os.path.exists(filename):
    return 1 
  try:
    f = open(filename,'w')
    count = 0
    while(count < 1):
      f.write('$File:$')
      f.write('File ID: $Id$')
      f.write('File Header: $Header$')
      f.write('File Author: $Author$')
      f.write('File Date: $Date$')
      f.write('File DateTime: $DateTime$')
      f.write('File Change: $Change$')
      f.write('File File: $File$')
      f.write('File Revision: $Revision$')
      f.write("This is a test for $file_name\n")
      count += 1

    f.flush()
    f.close()

  except Exception as e:
    p4error.exception(e) 

  return 0 

def find_files(treeroot):

  for base, dirs, files in os.walk(treeroot):
    return files

def integ_files(fq_port, client, user, process_name, cmd, count, dirname, depot_name, p4debug, p4error):

  dest_path = depot_name + process_name 
  src_path = depot_name + dirname 
  run_cmd = ['p4','-Ztrack','-p',fq_port,'-c',client,'-u',user]

  filter_slashes = re.compile(r'^//.+$')

  integ_txt = submit_txt = ""

  change_num = create_change.create_change(fq_port, client, user, process_name) 
  try:
    run_cmd.append(cmd) 

    if (count % 2) == 0: 
      run_cmd.append('-m')
      run_cmd.append('10')
    else:
      pass

    run_cmd.append('-c') 
    run_cmd.append(change_num) 
    run_cmd.append(src_path + '/...')               #//depot/test/...
    if cmd == 'integ':
      run_cmd.append(dest_path + '_' + str(count) + 'i/...') #//depot/testt1113_0i/...
    elif cmd == 'copy':
      run_cmd.append(dest_path + '_' + str(count) + 'c/...') #//depot/testt1113_0c/...
    elif cmd == 'merge':
      run_cmd.append(dest_path + '_' + str(count) + 'm/...') #//depot/testt1113_0m/...

    (integ_out,integ_err) = Popen(run_cmd, stdin=PIPE, stdout=PIPE).communicate()
    for each_line in integ_out.split(os.linesep):
      if filter_slashes.match(each_line):
        pass
      else:
        integ_txt += each_line + os.linesep
        
    sys.stdout.flush()

  except Exception as e:
    p4error.exception(e) 

  resolve_txt = ''
  if cmd == 'merge':
    resolve_txt = resolve_files(fq_port, client, user, cmd, p4debug, p4error)

  time.sleep(1)

  integ_txt = ''
  submit_txt = ''
  if (count % 2) == 0:
    (integ_txt, submit_txt) = submit_files(fq_port, client, user, 'integ', integ_txt, change_num, p4debug, p4error)
  else:
    shelve_files(fq_port, client, user, change_num, p4debug, p4error)
    (integ_txt, submit_txt) = submit_files(fq_port, client, user, 'integ', integ_txt, change_num, p4debug, p4error)
  
  return (integ_txt, resolve_txt, submit_txt)

def shelve_files(fq_port, client, user, change_num, p4debug, p4error):

  shelve_cmd = ['p4','-p', fq_port, '-c', client, '-u', user, 'shelve','-c', change_num]

  #p4 shelve -c <change>
  try:
    (shelve_out, shelve_err) = Popen(shelve_cmd, stdin=PIPE, stdout=PIPE).communicate()
    if shelve_err != None:
      print("ERROR: {0}".format(shelve_err)) 
      p4debug.debug(shelve_err)

  except Exception as e:
    p4error.exception(e)

  shelve_cmd.append('-p')

  #p4 shelve -c <change> -p
  try:
    (shelve_p, shelve_p_err) = Popen(shelve_cmd, stdin=PIPE, stdout=PIPE).communicate()
    if shelve_p_err !=None:
      print("ERROR: {0}".format(shelve_p_err)) 
      p4debug.debug(shelve_p_err)

  except Exception as e:
    p4error.exception(e)

  unshelve_cmd = ['p4', '-p', fq_port, '-c', client, '-u', user, 'unshelve', '-s', change_num]

  #p4 unshelve -s <change>
  try:
    (unshelve, unshelve_err) = Popen(unshelve_cmd, stdin=PIPE, stdout=PIPE).communicate()
    if unshelve_err !=None:
      print("ERROR: {0}".format(unshelve_err)) 
      p4debug.debug(unshelve_err)

  except Exception as e:
    p4error.exceptions(e)

  shelve_delete = ['p4', '-p', fq_port, '-c', client, '-u', user, 'shelve', '-d', '-c', change_num]

  #p4 shelve -f -d -c <change_num>
  try:
    (shelve_del_out, shelve_del_err) = Popen(shelve_delete, stdin=PIPE, stdout=PIPE).communicate()
    if shelve_del_err !=None:
      print("ERROR: {0}".format(shelve_del_err)) 
      p4debug.debug(shelve_del_err)

  except Exception as e:
    p4error.exceptions(e)
    
def resolve_files(fq_port, client, user, cmd, p4debug, p4error):

  resolve_txt = ''
  run_cmd = ['p4','-Ztrack','-p',fq_port,'-c',client,'-u',user]
  filter_slashes = re.compile(r'^//.+S')

  try:
    run_cmd.append('resolve')
    run_cmd.append('-at')

    (run_out, run_err) = Popen(run_cmd, stdin=PIPE, stdout=PIPE).communicate()
    for each_line in run_out.split(os.linesep):
      if filter_slashes.match(each_line):
        pass
      else:
        resolve_txt += each_line + os.linesep
    sys.stdout.flush()

  except Exception as e:
    p4error.exception(e) 

  return resolve_txt
  
def submit_files(fq_port, client, user, cmd, integ_txt, change_num, p4debug, p4error):

  submit_txt = ''
  run_cmd = ['p4','-Ztrack','-p',fq_port,'-c',client,'-u',user]
  filter_slashes = re.compile(r'^//.+$')
  try:
    run_cmd.append('submit')
    run_cmd.append('-c')
    run_cmd.append(change_num)

    (run_out, run_err) = Popen(run_cmd, stdin=PIPE, stdout=PIPE).communicate()
    for each_line in run_out.split(os.linesep):
      if filter_slashes.match(each_line):
        pass
      else:
        submit_txt += each_line + os.linesep
    sys.stdout.flush()

  except Exception as e:
    p4error.exception(e) 

  if cmd == 'integ':
    return (integ_txt, submit_txt)
  else:
    return submit_txt

def fast_open_files(cmd, fq_port, depot_name, client, user, path, dirname, integ_repeated, p4debug, p4error):
 
  file_num = 500 
  fq_port = str(fq_port)
  path_to_dir = path + os.sep + dirname  #t1997/test

  if not os.path.exists(path_to_dir):
    os.mkdir(path_to_dir)
    sys.stdout.flush()

  exists = 0
  for i in range(file_num):
    file_with_path = path_to_dir + os.sep + dirname + str(i) #t1997/test/test0
    exists = create_files(file_with_path,p4debug,p4error)
    if exists == 1:
      pass

  results = find_files(str(path_to_dir)) #t1997/test

  change_num = create_change.create_change(fq_port, client, user, '')

  cur_dir = os.getcwd()
  full_path = cur_dir + os.sep + path_to_dir + os.sep #/home/smoon/t1997/test/test0
  temp_fd = open(full_path + 'filelist.txt',"w")

  for each_file in results:
    temp_fd.write(full_path + each_file + "\n")

  temp_fd.close()
  
  open_cmd = ['p4', '-p', fq_port, '-c', client, '-u', user, '-x', full_path + 'filelist.txt',  cmd, '-c', change_num, '-t', 'text+C']

  try:

    print open_cmd
    (out,err) = Popen(open_cmd, stdin=PIPE, stdout=PIPE).communicate()
    sys.stdout.flush()
  
  except Exception as e:
    p4error.exception(e) 

  finally:
    open_cmd.remove(full_path + 'filelist.txt')
    open_cmd.remove('-x')

  submit_txt = submit_files(fq_port, client, user, cmd, '', change_num, p4debug, p4error)
  fast_branch(fq_port, depot_name, client, user, full_path, dirname, integ_repeated, p4debug, p4error)

def fast_branch(fq_port, depot_name, client, user, path, dirname, integ_repeated, p4debug, p4error):

  branch = ['p4', '-p', fq_port, '-c',client, '-u', user]

  max = integ_repeated 
  for i in range(max):
    branch.extend(['populate', '-d', 'submitting_change of populate_' + str(i), '//' + depot_name + '/' + dirname + '/...',
                   '//' + depot_name + '/' + dirname + '/' + dirname + '_' + str(i) + '/...'])

    try:
      (out, err) = Popen(branch, stdin=PIPE, stdout=PIPE).communicate()
      print out

    except Exception as e:
      p4error.exception(e)

    finally:
      branch.remove('//' + depot_name + '/' + dirname + '/' + dirname + '_' + str(i) + '/...')
      branch.remove('//' + depot_name + '/' + dirname + '/...')
      branch.remove('populate')

def open_files(cmd, fq_port, client, user, path, dirname, file_num, p4debug, p4error):
  
  fq_port = str(fq_port)
  path_to_dir = path + os.sep + dirname  #t1997/test

  if not os.path.exists(path_to_dir):
    os.mkdir(path_to_dir)
    sys.stdout.flush()

  exists = 0
  for i in range(file_num):
    file_with_path = path_to_dir + os.sep + dirname + str(i) #t1997/test/test0
    exists = create_files(file_with_path,p4debug,p4error)
    if exists == 1:
      pass

  results = find_files(str(path_to_dir)) #t1997/test

  change_num = create_change.create_change(fq_port, client, user, '')

  cur_dir = os.getcwd()
  full_path = cur_dir + os.sep + path_to_dir + os.sep #/home/smoon/t1997/test/test0
  temp_fd = open(full_path + 'filelist.txt',"w")

  for each_file in results:
    temp_fd.write(full_path + each_file + "\n")

  temp_fd.close()
  
  open_cmd = ['p4', '-p', fq_port, '-c', client, '-u', user, '-x', full_path + 'filelist.txt',  cmd, '-c', change_num, '-t', 'text+C']

  try:

    (out,err) = Popen(open_cmd, stdin=PIPE, stdout=PIPE).communicate()
    sys.stdout.flush()
  
  except Exception as e:
    p4error.exception(e) 

  finally:
    open_cmd.remove(full_path + 'filelist.txt')
    open_cmd.remove('-x')

  time.sleep(3)
  submit_txt = submit_files(fq_port, client, user, cmd, '', change_num, p4debug, p4error)

def sync_files(cmd, fq_port, client, user, dirname, depot_name, p4debug, p4error):
 
  fq_port = str(fq_port)

  sync_cmd = ['p4', '-p', fq_port, '-c', client, '-u', user, '-q', 'sync', '-f', depot_name + dirname + '/...']

  try:
    (out,err) = Popen(sync_cmd, stdin=PIPE, stdout=PIPE).communicate()
    p4debug.debug(err)
    sys.stdout.flush()

  except Exception as e:
    p4error.exception(e) 
