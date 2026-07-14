import time
start = time.perf_counter()

class X:
    def __init__(self, name: str, position: int, parent = None, depth = 0):
        self.list = []
        self.parent = parent
        self.index = -1
        self.depth = depth
        self.name = name
        self.pos = position
    def __call__(self):
        if self.parent == None:
            print(f"{self.name}(0, 0)" + " {")
        else:
            print("    " * (self.depth) + f"{self.name}({self.depth}, {self.index})" + " {")
        for ind, i in enumerate(self.list):
            if isinstance(i, X):
                i()
            else:
                print("    " * (self.depth + 1) + f"{i}({self.depth}, {ind})") 
        print("    " * (self.depth) + "}")
    def add(self, obj):
        self.list.insert(self.index+1, obj)
        self.index += 1
        return self
    def nest(self, name: str):
        self.list.insert(self.index+1, X(name, self.pos, self, self.depth + 1))
        self.index += 1
        return self.list[self.index]
    def remove(self):
        self.index -= 1
        return self.list.pop(self.index)
    def up(self):
        if self.parent == None:
            print("This is the root.")
            exit(1)
        else:
            return self.parent
    def down(self):
        return self.list[self.index]
    def next(self):
        if self.index + 1 <= len(self.list) - 1:
            self.index += 1
        else:
            print("No more item in the right.")
            exit(1)
        return self
    def previous(self):
        if self.index - 1 >= 0:
            self.index -= 1
        else:
            print("No more item in the left.")
            exit(1)
        return self

class Y:
    def __init__(self):
        self.root = X("RootNode", 0)
        self.tree = self.root
        self.history = {
            0 : -1
        }
        self.pointer = [0, -1] # Ind 0: Depth, Ind 1: Position
    def __call__(self):
        self.root()
    def add(self, obj):
        self.tree.add(obj)
        self.pointer[1] += 1
        self.history[self.pointer[0]] = self.pointer[1]
    def remove(self):
        self.tree.remove()
        self.pointer[1] -= 1
        self.history[self.pointer[0]] = self.pointer[1]
    def nest(self, name):
        self.tree = self.tree.nest(name) # Set the tree to the nest.
        self.history[self.pointer[0]] += 1 # Record the position change in the parent
        self.pointer[0] += 1 # Increase the depth
        self.pointer[1] = -1 # Since this is a new empty nest, set the position to -1
        self.history[self.pointer[0]] = -1 # Record the child position.
    def up(self):
        self.tree = self.tree.up()
        self.history.pop(self.pointer[0]) # Remove the nest record from the history.
        self.pointer[0] -= 1 # Decrease the depth.
        # Set the pointer position to the index of the parent.
        self.pointer[1] = self.history[self.pointer[0]]
    def down(self):
        item = self.tree.down()
        if isinstance(item, X):
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
        self.tree.next()
        self.pointer[1] += 1
        self.history[self.pointer[0]]  = self.pointer[1]
    def previous(self):
        self.tree.previous()
        self.pointer[1] -= 1
        self.history[self.pointer[0]] = self.pointer[1]

p = Y()

# enter root
p.nest("FunctionDefinition")

# function foo
p.add("function")
p.add("foo")

# parameters
p.nest("FunctionParameter")
p.add("a")
p.add("b")
p.up()

# function body
p.nest("FunctionBody")

# let x = a + b * 2
p.add("let")
p.add("x")
p.add("=")

p.nest("StatementDefinition")
p.add("a")
p.add("+")
p.add("b")
p.add("*")
p.up()

# if (x > 10)
p.nest("IfDefinition")
p.add("if")

p.nest("IfTest")
p.add("x")
p.add(">")
p.add(10)
p.up()

# if-body
p.nest("IfBody")

# while (x < 100)
p.nest("WhileDefinition")
p.add("while")

p.nest("WhileTest")
p.add("x")
p.add("<")
p.add(100)
p.up()

# while-body
p.nest("WhileBody")
p.add("x")
p.add("=")

p.nest("StatementDefinition")
p.add("x")
p.add("+")
p.add(1)
p.up()

p.up()   # end while-body
p.up()   # end while

# return x
p.add("return")
p.add("x")

p.up()   # end if-body

# else
p.add("else")
p.nest("ElseBody")
p.add("return")
p.add(0)
p.up()

p.up()   # end if

# end function body
p.up()

# end function
p.add("end")

# back to root
p.up()

# dump tree
p()

stop: float =time.perf_counter()
print(stop - start)

