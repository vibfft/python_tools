import unittest, os, sys, re
from modules.p4 import P4 
#
#There are two test cases in this class:
#They are:
#
#test_branch and test_copy
#
#Before each test case, "setUp" is run.  It creates
#user as well as client
#
#And then there is "assertTrue" check to see whether it passed
#the test
#
#After that, there is "tearDown" which reverts the condition from where it started.
#
#If you want to start completely fresh, you can always delete anything under "p4root" directory.
#
#By default, the Server binary needs to be in the path and the Server is started automatically
#through rsh port.
#

class Test_Integ(unittest.TestCase):

  global p4
  p4 = P4()
  def setUp(self):

    msg = " Running setUp "
    print
    print(msg.center(80,'#'))
    p4.set_user(p4.create_user('smoon'))
    p4.set_client(p4.create_client('test_ws',p4.get_user()))

  def test_branch(self):

    re_branched = re.compile(r'^\d+ files branched \(change \d+\)\.$') 
    p4.create_files('test_ws/test_one.txt')
    p4.run('add','test_ws/test_one.txt')
    p4.run('submit','-d','test_one_branched')
    (out,err) = p4.run('populate','test_ws/test_one.txt','test_ws/test_two.txt')

    for each_line in out.split(os.linesep):
      m = re_branched.match(each_line)
      if m is not None:
        self.assertTrue(True)

  def test_copy(self):
 
    re_copied = re.compile(r'^[<>]') 
    p4.create_files('test_ws/test_one.txt')
    p4.run('add','test_ws/test_one.txt')
    p4.run('submit','-d','test_one_submitted')
    p4.run('copy','test_ws/test_one.txt','test_ws/test_two.txt')
    p4.run('submit','-d','test_one_copied')
    p4.run('edit','test_ws/test_one.txt','test_ws/test_two.txt')
    (out,err) = p4.run('diff','test_ws/test_one.txt','test_ws/test_two.txt')
  
    for each_line in out.split(os.linesep):
      m = re_copied.match(each_line)
      if m is not None:
        self.assertTrue(False)
      else:
        self.assertTrue(True)

  def tearDown(self):

    msg = " Running tearDown "
    print
    print(msg.center(80,'#'))
    p4.run('revert','//...')
    p4.run('sync','//...#none')
    p4.run('client','-d',p4.get_client())
    p4.run('user','-d',p4.get_user())
    p4.run('obliterate','-y','//...')

def main():

  unittest.main()

if __name__ == '__main__':
  main()
