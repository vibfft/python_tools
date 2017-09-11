#!/usr/bin/env python

import sys, pprint
from pprint import pprint

class Mine_Sweeper(object):

  def __init__(self, col, row, pos_set):

    self.col = int(col)     #column size
    self.row = int(row)     #row size
    self.pos_set = pos_set  #set of positions
    self.matrix = []        #matrix of mines

  def create_matrix(self):

    #initialize the matrix with zero
    row_list = []
    for c in range(self.col):
      for r in range(self.row):
        row_list.append(0)
      self.matrix.append(row_list)
      row_list = []
    #print self.matrix

  def create_mine(self):

    #build a matrix with mines
    for each_list in self.pos_set:
      row = int(each_list[1])
      col = int(each_list[0])

      if self.check_out_of_bound(row,col):
        pass
      elif self.check_adjacent_cell(row,col):
        pass
      elif self.check_mine_exists(row,col):
        pass
      else:
        self.matrix[row][col] = 'x'
        #print("R: {0}, C: {1}".format(row, col))
        self.permut_check(row, col)
    return self.matrix

  def display_results(self):

    #print the finished matrix
    accum = '' 
    for each_list in self.matrix:
      for each_value in each_list:
        accum += str(each_value) + ' '
      print accum
      accum = '' 

  def check_out_of_bound(self, row, col):
    if row >= self.row or col >= self.col:
      return True 
    return False 
  def check_adjacent_cell(self, row, col):
    if row == -1 or col == -1:
      return True 
    return False 

  def check_mine_exists(self, row, col):
    if self.matrix[row][col] == 'x':
      return True 
    return False 

  def check_cell(self, row, col):

    if self.check_out_of_bound(row,col):
      pass
    elif self.check_adjacent_cell(row,col):
      pass
    elif self.check_mine_exists(row,col):
      pass
    else:
      self.matrix[row][col] += 1 

  def permut_check(self, row, col):
   
    #out of bound 
    if row >= self.row or col >= self.col:
      pass
    else:
      # row - 1, col - 1
      (lambda x,y: self.check_cell(x, y))(row - 1, col - 1)

      # row - 1, col
      (lambda x,y: self.check_cell(x, y))(row - 1, col)

      # row - 1, col + 1
      (lambda x,y: self.check_cell(x, y))(row - 1, col + 1)

      # row    , col - 1  
      (lambda x,y: self.check_cell(x, y))(row , col - 1)

      # row    , col + 1
      (lambda x,y: self.check_cell(x, y))(row, col + 1)

      # row + 1, col - 1
      (lambda x,y: self.check_cell(x, y))(row + 1, col - 1)
    
      # row + 1, col
      (lambda x,y: self.check_cell(x, y))(row + 1, col)

      # row + 1, col + 1
      (lambda x,y: self.check_cell(x, y))(row + 1, col + 1)

  @staticmethod
  def process_input(input_array):

    size_row = size_col = 0 
    col = row = 0
    pos_set = set()   #guard against duplicate coordinates 
    matrix_index = pos_index = -1

    pprint(input_array)
    sentinel = ''
    for each_line in input_array.split('\n'):
      if each_line == '':
        break
      #print each_line
      str_data = each_line.strip()      #strip the line-ending
      matrix_index = str_data.find('x') #find the input line with matrix size
      pos_index = str_data.find(',')    #find the input line with coordinates
      if matrix_index != -1:
        size_col,size_row = str_data[0:matrix_index],str_data[matrix_index + 1:] 
        #print("size_col: {0} size_row: {1}".format(size_col,size_row))
      if pos_index != -1:
        col,row = str_data[0:pos_index],str_data[pos_index + 1:] 
        if col.isdigit() and row.isdigit():
          pos_set.add((col,row))
        #print("col: {0} row: {1}".format(col,row))
      matrix_index = -1
      pos_index = -1

    m_obj = Mine_Sweeper(size_col, size_row, pos_set)
    m_obj.create_matrix()
    matrix = m_obj.create_mine()
    m_obj.display_results()
  
    return matrix

#def main(): 
#
#  #if not the input file, but a list of strings with '' sentinel
#  input_array = []
#  sentinel = ''
#  for line in iter(raw_input, sentinel):
#    input_array.append(line)
#
#  col, row, pos_set = Mine_Sweeper.process_input(input_array)
#
#  m_obj = Mine_Sweeper(col, row, pos_set)
#  m_obj.create_matrix()
#  m_obj.create_mine()
#
#if __name__ == '__main__':
#  main()
