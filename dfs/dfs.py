#!/usr/bin/python

graph = {'a':set(['b','c']),
         'b':set(['a','d','e']),
         'c':set(['a','f']),
         'd':set(['b']),
         'e':set(['b','f']),
         'f':set(['e']),
        }

#   a
#  / \
# c   b
#    / \
#   d   e
#      / 
#     f

def dfs(graph, start):
  visited, stack = set(), [start]
  while stack:
    vertex = stack.pop()
    print("vertex: {0}".format(vertex,end=''))
    if vertex not in visited:
      visited.add(vertex)
      print("graph[{0}]: {1}, visited: {2}".format(vertex,graph[vertex],visited))
      stack.extend(graph[vertex] - visited)
      print("DFS: {0}".format(stack))
  return visited

def main():

  print("GRAPH: {0}".format(graph))
  dfs(graph,'a')

if __name__ == '__main__': 
  main()
