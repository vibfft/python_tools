import os, unittest

def main():

  #set up p4root directory
  if os.path.exists('p4root'):
    pass
  else:
    os.mkdir('p4root') 

  cwd = os.getcwd() 
  loader = unittest.TestLoader()

  #finds all the tests from test_cases directory
  #it looks for "test*.py" by default   
  tests = loader.discover(os.path.join(cwd,'test_cases'))

  #runs all test cases
  unittest.TextTestRunner(verbosity=2).run(tests)

if __name__ == '__main__':
  main()
