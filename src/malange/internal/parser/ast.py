'''

    malange.internal.parser.ast

    Class to make nodes, which is required for
    creating Abstract Syntax Tree (AST)

    The way it is designed is via a recursive node system.

    RootNode {
        ParentNode {
            ChildNode { # Empty node.
            }
            "abc"
            "aaa"
        }
        "xyz"
    }

    This is stored in the ASTNode. When you initialize a node,
    The node is empty. You can know by seeing the self.index = -1.
    To add item, you add via add() method (which will move the self.index
    to the right, aka self.index += 1.If you remove an item via remove()
    well the opposite.

    If you choose "nesting". The node will add an item that is a node,
    thus recursive.

    You can do this:

    init = ASTNode("RootNode", 0) # RootNode
    init.add("abc"
        ).add("xyz"
        ).previous(
        ).nest(
        ).add("cde"
        ).up(
        )

    ASTWrapper is just a way to make the code like this:

    init.add("abc")
    init.add("xyz")
    init.previous()
    init.nest()
    init.add("cde")
    init.up()

    ASTWrapper can print the entire tree too via print() method.

'''

from malange.api.error import ErrorManager

error = ErrorManager()

class ASTNode:
    '''
        This is the class for storing nodes.
    '''
    def __init__(self, name: str, position: int, parent = None, depth = 0):
        '''
            Initialize the class.

            parameters:
                name:     str     = The name of the node.
                position: int     = The index of the node within the parent node.
                parent:   ASTNode = The reference to the parent node. None = The node doesn't have
                                    a parent node, aka the node is a root node.
                depth:    int     = The position of the node within the nesting tree. 0 = Root node.
        '''
        self.list:   list           = []       # Items that the node holds.
        self.parent: ASTNode | None = parent   # The parent node.
        self.index:  int            = -1       # Index that keep tracks of the pointer position of self.list
        self.depth:  int            = depth    # The position of the node within the nesting tree.
        self.name:   str            = name     # Name of the node.
        self.pos:    int            = position # Position of the node within the self.list of the parent node.

    def __call__(self):
        '''Call the class to print the entire tree.'''
        if self.parent == None:
            print(f"{self.name}(0, 0)" + " {")
        else:
            print("    " * (self.depth) + f"{self.name}({self.depth}, {self.index})" + " {")
        for ind, i in enumerate(self.list):
            if isinstance(i, ASTNode): # If the item is a node.
                i()
            else: # If the item is a generic item.
                print("    " * (self.depth + 1) + f"{i}({self.depth}, {ind})") 
        print("    " * (self.depth) + "}")
    def __update_pos(self):
        '''Update position of each child nodes.'''
        for ind, i in enumerate(self.list):
            if isinstance(i, ASTNode):
                i.pos = ind

    def add(self, obj):
        '''Add the class. parameters: obj: any = Any kind of object you want to add.'''
        self.list.insert(self.index+1, obj)
        self.index += 1
        self.__update_pos() # Update child nodes position.
        return self
    def nest(self, name: str):
        '''Similar to add() method but you add new node and return the new node instead.'''
        self.list.insert(self.index+1, ASTNode(
            name, self.pos, self, self.depth + 1))
        self.index += 1
        self.__update_pos()
        return self.list[self.index]
    def remove(self):
        '''Remove an item/node.'''
        obj = self.list.pop(self.index)
        self.index -= 1
        self.__update_pos()
        return obj

    def up(self):
        '''Return the parent node.'''
        if self.parent == None:
            error({
            'component' : 'internal.parser.noparentnode',
            'message'   : 'The node does not have a parent node. It is a root node',
            'index'     : -1
            })
        else:
            return self.parent
    def down(self):
        '''Return the item or a child node.'''
        if self.list == []:
            error({
            'component' : 'internal.parser.emptynode',
            'message'   : 'The node is empty.',
            'index'     : -1
            })
        else:
            return self.list[self.index]

    def next(self):
        '''Select the next item within the list.'''
        if self.index + 1 <= len(self.list) - 1:
            self.index += 1
        else:
            error({
            'component' : 'internal.parser.noitemontheright',
            'message'   : 'There is no item/node in the right of the pointer.',
            'index'     : -1
            })
        return self
    def previous(self):
        '''The opposite of next()'''
        if self.index - 1 >= 0:
            self.index -= 1
        else:
            error({
            'component' : 'internal.parser.noitemontherleft',
            'message'   : 'There is no item/node in the left of the pointer.',
            'index'     : -1
            })
        return self

class ASTWrapper:
    '''
        The wrapping class that makes node management
        better (as has been explained in the docstring)
        To do that this is how:
        - self.root holds the reference to the root node.
        - self.tree holds the ref to the node we are handling,
          it can be a child node or any node.
        - self.history keeps track of the pointer position on
          each depth. e.g.
          0 : 2 -> depth 0 (root), position 2 (position starts at 0 btw)
          1 : 4 -> depth 1 (first layer), position 4
          2 : -1 -> depth 2, node is still empty.
        - self.pointer holds the current pointer info,
          [0, -1] -> The pointer is in depth 0, -1 means the root node is empty.
        - Whenever you exit a node via up(), you delete the history. Thus when
          you go back, you expect position -1 for empty node, position 0 or first item
          for non-empty node.
    '''

    def __init__(self):
        '''Initialize the class.'''
        self.root:    ASTNode        = ASTNode("RootNode", 0) # The root node.
        self.tree:    ASTNode        = self.root # Any node the class is handling.
        self.history: dict[int, int] = {0 : -1}
        self.pointer: list[int]      = [0, -1] # Ind 0: Depth, Ind 1: Position
    def __call__(self):
        '''Wrapper for __call__ of ASTNode'''
        self.root() # Calls the root to print the entire tree.

    def add(self, obj):
        '''Add an item.'''
        self.tree.add(obj)
        self.pointer[1] += 1
        self.history[self.pointer[0]] = self.pointer[1]
    def remove(self):
        '''Remove an item.'''
        self.tree.remove()
        self.pointer[1] -= 1
        self.history[self.pointer[0]] = self.pointer[1]
    def nest(self, name):
        '''Add a child node, enter the child node immediately.'''
        self.tree = self.tree.nest(name) # Set the tree to the nest.
        self.history[self.pointer[0]] += 1 # Record the position change in the parent
        self.pointer[0] += 1 # Increase the depth
        self.pointer[1] = -1 # Since this is a new empty nest, set the position to -1
        self.history[self.pointer[0]] = -1 # Record the child position.

    def up(self):
        '''Go back to the parent node.'''
        self.tree = self.tree.up()
        self.history.pop(self.pointer[0]) # Clear the history for the child node.
        self.pointer[0] -= 1 # Decrease the depth.
        # Set the pointer position to the position of the parent node.
        self.pointer[1] = self.history[self.pointer[0]]
    def down(self):
        '''Go to the child node.'''
        item = self.tree.down()
        if isinstance(item, ASTNode):
            self.tree = item # Set the tree to the child.
            self.pointer[0] += 1 # Increase the depth of the pointer.
            if self.tree.list == []: # If it is still an empty child
                self.pointer[1] = -1 # Set it to -1, aka empty child
            else: # If not give 0.
                self.pointer[1] = 0 # Since this means the first item of the child
            self.history[self.pointer[0]] = self.pointer[1] # Add to the history.
        else:
            return item # If it is not a nest, return the fundamental block

    def next(self):
        '''Select the next item/node.'''
        self.tree.next()
        self.pointer[1] += 1
        self.history[self.pointer[0]]  = self.pointer[1]
    def previous(self):
        '''Opposite of next()'''
        self.tree.previous()
        self.pointer[1] -= 1
        self.history[self.pointer[0]] = self.pointer[1]

