import unittest
import os, sys

class Test_Lockless(unittest.TestCase):

  def setUp(self):
    msg = "Running setUp"
    print
    print(msg.center(80,'#'))

  def tearDown(self):
    msg = "Running tearDown"
    print
    print(msg.center(80,'#'))

  def test_annotate(self):

    self.a = 'annotate'
    self.b = 'annotate'
    self.assertEqual(self.a, self.b)

  def test_fstat(self):
 
    self.a = 'fstat'
    self.b = 'fstat'
    self.assertEqual(self.a, self.b)

def main():
  unittest.main()

if __name__ == '__main__':
  main()
