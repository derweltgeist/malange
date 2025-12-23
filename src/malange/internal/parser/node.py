'''

    malange.internal.parser.node

    Class to make nodes, which is required for
    creating Abstract Syntax Tree (AST)

'''

class Node:
    '''Used to represent a node.'''

    def __init__(self, counter: int, parent = None):
        self.__parent = parent
        self.__counter = counter
        self.__list = []

    def add(self, indicator, item):
        self.__list.append(item)

    def remove(self, item):
        self.__list.remove(item)

class Pointer:
    def __init__(self):
        self.__tree: Node = Node(0)

    def add(self, item):
        pass
        
