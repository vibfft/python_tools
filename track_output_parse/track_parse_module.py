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
#
#Module to parse the track output from a Perforce command.
#
#e.g.:
#  track_parse(<output>, <title (cmd name)>, <db_name>, <num_of_files>, <bytes>, <header_include_boolean>, <file_handle>) 
#
#

import re, sys, os

class CMD_Dict(dict):

  def __init__(self, *arg, **kw):
    super(CMD_Dict, self).__init__(*arg, **kw) 

    self.CMD = {}
    self.db_name = {}
    self.param = {}
    self.stat_array = [] 
    self.lapse_time = {}

  def read_input(self, output, cmd):

    db    = re.compile(r'^---\s(db\.\w+).*$')
    lapse = re.compile(r'^---\s+(lapse)\s+(\S+)$')
    usage = re.compile(r'^---\s(usage)\s(.+)$')
    rpc   = re.compile(r'^---\s(rpc)\s(.+)$')
    param = re.compile(r'^---\s+(\w+)\s(.+)$')

    db_name = ''

    for each_line in output.split(os.linesep):

      m_db    = db.match(each_line)
      m_lapse = lapse.match(each_line)
      m_usage = usage.match(each_line)
      m_rpc   = rpc.match(each_line)

      if m_lapse is not None:
        self.lapse_time['all'] = {'lapse_time':{'time':m_lapse.group(2)}}
      elif m_usage is not None:
        pass
      elif m_rpc is not None:
        pass
      elif m_db is not None:
        #print("track parse m_db: {0}".format(each_line))
        db_name = m_db.group(1)
      elif each_line != '':
        m_param = param.match(each_line)
        #print("track parse else: {0}".format(each_line))
        #print("DB_NAME GROUP: {0}".format(db_name))
        if m_param is not None:
          #print("track parse m_param: {0}".format(each_line))
          param_stat = db_name + "#" + m_param.group(1)
          stat_array = m_param.group(2).split(' ')

          if param_stat.split('#')[1] == 'pages':
            #print stat_array[0], stat_array
            self.param[param_stat + '_' + stat_array[0]] = self.stat_pages('pages', stat_array)  #params and its stats 

          elif param_stat.split('#')[1] == 'locks':
            self.param[param_stat] = self.stat_locks('locks', stat_array)  #params and its stats 

          elif param_stat.split('#')[1] == 'total':
            self.param[param_stat] = self.stat_max_total_locks('total', stat_array)  #params and its stats 

          elif param_stat.split('#')[1] == 'max':
            self.param[param_stat] = self.stat_max_total_locks('max', stat_array)  #params and its stats 

          self.db_name[db_name] = self.param   #different params for each table
          self.CMD[cmd] = self.db_name         #top dict contains the db names

  def stat_pages(self, param_name, stats):

    pages = {}
    if stats[0] == 'in+out+cached':
      #pages in+out+cached 277+711+96, stats[0] == in+out+cached
      pages = { param_name + '_' + page_io:num_page_io 
                for page_io, num_page_io in zip(stats[0].split('+'), stats[1].split('+')) }
    elif stats[0] == 'split':
      #pages split internal+leaf 2+0, stats[0] == split
      pages = { param_name + '_' + stats[0] + '_' + page_split:num_page_split 
                for page_split, num_page_split in zip(stats[1].split('+'), stats[2].split('+')) }
    elif stats[0] == 'reordered':
      #pages reordered internal+leaf 2+0, stats[0] == reordered 
      pages = { param_name + '_' + stats[0] + '_' + page_reordered:num_page_reordered 
                for page_reordered, num_page_reordered in zip(stats[1].split('+'), stats[2].split('+')) }
    return pages

  def stat_locks(self, param_name, stats):

    #locks read/write 1/64 rows get+pos+scan put+del 0+1+1 6400+0, stats[0] == read/write
    locks_acq      = { read_write + '_' + param_name : num_locks 
                       for read_write, num_locks in zip(stats[0].split('/'), stats[1].split('/')) }

    locked_rows    = { param_name + '_' + stats[2] + '_' + rows_scan: num_rows 
                       for rows_scan, num_rows in zip(stats[3].split('+'), stats[5].split('+')) }

    locked_rows_io = { param_name + '_' + stats[2] + '_' + rows_io: num_rows 
                       for rows_io, num_rows in zip(stats[4].split('+'), stats[6].split('+')) }

    return dict(locks_acq.items() + locked_rows.items() + locked_rows_io.items())

  def stat_max_total_locks(self, param_name, stats):
    #total lock wait+held read/write 0mx+0ms/0ms+34ms, stats[0] == lock
    #  max lock wait+held read/write 0mx+0ms/0ms+34ms, stats[0] == lock
    if param_name == 'total':
      total_read_lock = { param_name + '_' + stats[2].split('/')[0] + '_' + stats[0] + '_' + wait_held : time_wait_held 
                          for wait_held, time_wait_held in zip(stats[1].split('+'), stats[3].split('/')[0].split('+'))}
      total_write_lock = { param_name + '_' + stats[2].split('/')[1] + '_' + stats[0] + '_' + wait_held : time_wait_held 
                          for wait_held, time_wait_held in zip(stats[1].split('+'), stats[3].split('/')[1].split('+'))}

      return dict(total_read_lock.items() + total_write_lock.items())

    elif param_name == 'max':
      max_read_lock = { param_name + '_' + stats[2].split('/')[0] + '_' + stats[0] + '_' + wait_held : time_wait_held 
                          for wait_held, time_wait_held in zip(stats[1].split('+'), stats[3].split('/')[0].split('+'))}
      max_write_lock = { param_name + '_' + stats[2].split('/')[1] + '_' + stats[0] + '_' + wait_held : time_wait_held 
                          for wait_held, time_wait_held in zip(stats[1].split('+'), stats[3].split('/')[1].split('+'))}

      return dict(max_read_lock.items() +  max_write_lock.items())

def split_unit_value(input_value):

  ms_re = re.compile(r'(.*)(ms)$')

  ms = ms_re.match(input_value)

  if ms is not None:
    #print("time, {0}, {1}".format(ms.group(1), ms.group(2)))
    return("time", ms.group(1), ms.group(2))

  else: 
    #print("count, {0}, rows".format(input_value))
    return("count", input_value, "rows")

    print("time, {0}, {1}".format(ms.group(1), ms.group(2)))

def split_lapse_time(input_value):

  sec_re = re.compile(r'(.*)(s)$')

  sec = sec_re.match(input_value)
  if sec is not None:
    #print("{0}, {1}".format(sec.group(1), sec.group(2)))
    return(sec.group(1), sec.group(2))

  else:
    return('value',None)


def track_parse(output, cmd, table, files, bytes, header, f):

  c = CMD_Dict()
  c.read_input(output, cmd)

  #f.write("TABLE:PARAM:VALUETYPE:UNIT:VALUE\n")

  if header == True:
    print("TABLE:PARAM:VALUETYPE:UNIT:VALUE")
    print("{0}:{1}:{2}:{3}:{4}".format('all', 'files', 'count', 'files', files))
    print("{0}:{1}:{2}:{3}:{4}".format('all', 'bytes', 'count', 'bytes', bytes))
    f.write("{0}:{1}:{2}:{3}:{4}\n".format('all', 'files', 'count', 'files', files))
    f.write("{0}:{1}:{2}:{3}:{4}\n".format('all', 'bytes', 'count', 'bytes', bytes))

    for k, v in c.lapse_time['all']['lapse_time'].iteritems():
      (real_val, unit) = split_lapse_time(v)
      f.write("{0}:{1}:{2}:{3}:{4}\n".format('all', 'lapse_time', k, unit, real_val))
      print("{0}:{1}:{2}:{3}:{4}".format('all', 'lapse_time', k, unit, real_val))

  for cmd in c.CMD:
    for db_name in c.CMD[cmd]:
      for param, details in c.CMD[cmd][db_name].iteritems():
        if db_name == param.split('#')[0]:
          for k, v in c.CMD[cmd][db_name][param].iteritems():
            #print("db_name: {0}, k: {1}, v: {2}".format(db_name, k,v))
            if db_name == table:
              #print("DB_NAME: {0}, TABLE_Input: {1}".format(db_name, table))
              #print("{0}: {1}: {2}:  {3}: {4}".format(cmd, db_name, param.split('#')[1], k, v))
              (valuetype, real_val, unit) = split_unit_value(v)
              f.write("{0}:{1}:{2}:{3}:{4}\n".format(db_name, k, valuetype, unit, real_val))
              print("{0}:{1}:{2}:{3}:{4}".format(db_name, k, valuetype, unit, real_val))
