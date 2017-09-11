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
# Author: Stephen Moon
# Date: 3/5/09
# Last Modified Date: 7/13/09
#
# Summary: Retrieves Perforce binaries or ASCII files from ftp.perforce.com
#
# Usage:
#
#   Unix/Linux: 
#	Invoke it from the command line (make sure that Python 2.4 or higher 
#	release version is installed although it should work with older versions
# 
#   Windows: 
#	Need to have Python 2.4 or higher release version installed
#	Remove the She-bang line and invoke it by typing "python fetch.py"
#	at the command prompt. 	
#
#*******************************************************************************

import ftplib, re, os, sys, getpass

HOST = 'ftp.perforce.com'
DIR_NAME = 'perforce'

#holds each displayed line entry
class DirEntry(object): #inherits from class object
   def __init__(self,line): #only accept one argument line
	self.parts = line.split(None,8) #split into 8 parts for each line

   def isValid(self):
	return len(self.parts) >= 6 #if num of parts greater than 6 then it's valid

   def getType(self):
	return self.parts[0][0] #get the very first character on the line (i.e. 

   def getFilename(self):
	if self.getType() != 'l': #if it is not a link
	   return self.parts[-1] #return the last part
	else:
	   return self.parts[-1].split(' -> ', 1)[0] #if it is, return shortcut

   def getSize(self):
	if self.getType() == '-':
	   return int(self.parts[4])/1024

   def getMonth(self):
	if self.getType() == '-':
	   return self.parts[5]

   def getDay(self):
	if self.getType() == '-':
	   return self.parts[6] 

   def getLinkDest(self): #return the original destination of link
	if self.getType() == 'l':
	   return self.parts[-1].split(' -> ', 1)[1]
	else:
	   raise RuntimeError, "getLinkDest() called on non-link item"

#creates a key (fname) and value (line for the filename)
class DirScanner(dict): #inherits from class dict 
   def addline(self,line): #only accepts one arugment line
	obj = DirEntry(line)
	if obj.isValid(): #line object contains more than 6 parts
	   self[obj.getFilename()] = obj #creates a key/value pair, key = fname

#downloads a file
def downloadFile(ftpobj, filename):
   ftpobj.voidcmd("Type I")

   #creating of a set of 0...100 incremented by 10
   s = set([])
   for i in range(0,100,10):
     s.add(i)
   
   #based on the filename, it returns a tuple of the data connection and the expected
   #size of data
   datasock, estimatedSize = ftpobj.ntransfercmd("RETR %s" % filename)
   transbytes = 0
  
   fd = file(filename, 'wb')
      
   while True:
	buf = datasock.recv(2048)
	if not len(buf):
	   break;
	fd.write(buf)
	transbytes += len(buf)
	percent = 100.0*float(transbytes/float(estimatedSize))

        if (int(percent) % 10) == 0 and int(percent) in s:
	   s.remove(int(percent)) #remove the percent from the set

	   sys.stdout.write("%s: Received %d " % (filename, transbytes))
	   if estimatedSize:
	      sys.stdout.write("of %d bytes (%0.1f%%)\n" % (estimatedSize,
	      100.0 * float(transbytes) / float(estimatedSize)))
	   else:
	      sys.stdout.write("bytes")
   fd.close()
   datasock.close()
   ftpobj.voidresp()
   sys.stdout.write("\n")

#log in anonymously to ftp.perforce.com and then change directory to perforce
def initialize(): 
   try:
   	ftp = ftplib.FTP(HOST)
   except (socket.error, socket.gaierror), e:
   	print 'Error: cannot reach "%s"' % HOST
   	return
   print '\n*** Connected to host "%s" ***' % HOST 

   while True:
      print '\nPlease log in with "anonymous" as a login name \
             \nand type your email address as your password\n'
      username = raw_input("login: ")
      password = getpass.getpass("password: ")
      
      try:
         if ftp.login(username,password):
	    break
      except ftplib.error_perm:
         print 'Error: wrong login and/or password'
         print 'Try again'   
	

   try:
	ftp.cwd(DIR_NAME)
   except ftplib.error_perm:
	print '\nError: cannot change directory to "%s"' % DIR_NAME
        print 'Changed the directory to a default directory'
   
   return ftp

#displays the entries for a chosen directory
def displayFiles(ftp):

   data = {} 
   data = DirScanner() #create data object of class DirScanner
   ftp.dir(data.addline) #add lines to dict when dir is run

   f = '[FILE]'
   d = '[DIR]'

   keys = data.keys() #get the keys
   keys.sort() #sort it

   #print it to the sorted filenames
   print "\nCurrent Working Directory: ",ftp.pwd(),"\n"
   for i,eachEntry in enumerate(keys):
      if data[eachEntry].getType() == '-': #DirEntry object using fileName key
         print '%2d:%6s %5sK %-3s %2s %s' % (i,f,data[eachEntry].getSize(),
		data[eachEntry].getMonth(),data[eachEntry].getDay(),eachEntry)
      elif data[eachEntry].getType() == 'd': #same as above but directory
         print '%2d:%6s %s' % (i,d,eachEntry)
         #print '('+str(i)+'):\t [DIR] ',eachEntry
   print '\n%2s: go up one directory' % 'u'
   print '%2s: exit\n' % 'e'
   
   return data


#main starts here

def main():
  
   ftp = initialize()
   data = displayFiles(ftp) 
   choice = raw_input("Choose a directory or file from the above choices: ")

   while True:

     try:
	
   	if choice is 'u':
	   ftp.cwd("..")
   	elif choice is 'e':
	   break;
   	elif choice.isalpha():
	   print "\n*** You have entered alpha character other than given choices ***"
   	elif(int(choice) <= len(data) - 1): 

	   keys = data.keys()
	   keys.sort() # filenames sorted
	   for i, fileName in enumerate(keys):
	      if i == int(choice):
	         if data[fileName].getType() == '-': #DirEntry object using fileName key
			try:
		   	   downloadFile(ftp,fileName)
			except ftplib.error_perm:
			   print 'Error: cannot download file "%s"' % fileName
			   os.unlink(fileName)
			else:
			   print '*** Downloaded "%s" to current local directory ***' % fileName	

	         elif data[fileName].getType() == 'd': #same as above but directory
			try:
		   	   ftp.cwd(fileName)
			except ftplib.error_perm:
			   print 'Error: cannot cd to "%s"' % fileName
			   return
   	else:
	   print "\n*** You have made an invalid choice ***"

     except ValueError:
   	print "\n*** You have entered alphanumeric character other than given choices ***"

      
     data = displayFiles(ftp) 
     choice = raw_input("Choose a directory or file from the above choices: ")

ftplib.FTP(HOST).quit()

if __name__ == '__main__':
	main()
