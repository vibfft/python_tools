#!/usr/bin/env python

import unittest
from mine_sweep_unit import Mine_Sweeper

class TestMine(unittest.TestCase):

  def testMine_Sweeper(self):

    mine = Mine_Sweeper.process_input('5x5\n'
                        '0,0\n'
                        '1,0\n'
                        '2,2\n'
                        '4,4\n')
    result = [['x','x',1,0,0],[2,3,2,1,0],[0,1,'x',1,0],[0,1,1,2,1],[0,0,0,1,'x']]

    assert result == mine 

  def testCheck_Out_of_Bound(self):

    mine = Mine_Sweeper.process_input('5x5\n'
                        '0,0\n'
                        '1,0\n'
                        '2,2\n'
                        '4,4\n'
                        '5,5\n')
    result = [['x','x',1,0,0],[2,3,2,1,0],[0,1,'x',1,0],[0,1,1,2,1],[0,0,0,1,'x']]

    assert result == mine 

  def testNegative_Index(self):

    mine = Mine_Sweeper.process_input('5x5\n'
                        '0,0\n'
                        '1,0\n'
                        '2,2\n'
                        '4,4\n'
                        '-1,-1\n')
    result = [['x','x',1,0,0],[2,3,2,1,0],[0,1,'x',1,0],[0,1,1,2,1],[0,0,0,1,'x']]

    assert result == mine 

  def testNon_Numeric(self):

    mine = Mine_Sweeper.process_input('5x5\n'
                        '0,0\n'
                        '1,0\n'
                        '2,2\n'
                        '3,sbc\n'
                        '4,4\n'
                        'a,-1\n'
                        '0,=\n')

    result = [['x','x',1,0,0],[2,3,2,1,0],[0,1,'x',1,0],[0,1,1,2,1],[0,0,0,1,'x']]

    assert result == mine 

if __name__ == '__main__':
  unittest.main()
