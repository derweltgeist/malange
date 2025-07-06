'''

    malange.transpiler.parser.malap

    malap = Malange Parser

    Parser for Malange tokens. malap will construct an
    ast from the tokens. It will also check for any syntax
    errors. But runtime errors won't be checked.

'''

import re
from typing import Union, Callable

from malange.internal.transpiler.tokenizer.token import MalangeToken as Token

error = Error()

class MalangeObject:
    '''Object for Malange parsers.'''
    def __init__(self, name: str, value: any,
                 parent: MalangeNode, watch: Callable[[MalangeNode], None]) -> None:
        self.__name: str                             = name
        self.__value:  any                           = value
        self.__watch:  Callable[[MalangeNode], None] = watch
        self.__parent: MalangeNode                   = parent
    def value(self, data: any) -> None:
        self.__value: any = data
    def nest(self) -> None:
        self.__value: any = MalangeNode(self.__parent)
        self.__watch(self.__value) # Tell the wrapper the new node.

class MalangeNode:
    '''
    Node for Malange parsers.
    '''

    def __init__(self, parent: MalangeNode = None) -> None:
        '''
        Create the data and store the parent.
        '''
        self.__data = {}
        self.__parent = parent

    def add(self, name: str, wrapper: MalangeTree, value: any = None) -> MalangeObject:
        '''
        Add an item to the data list.
        parameters:
            name: str = The name of the item.
            wrapper: MalangeTree = The wrapper instance class.
            value: any = The starting value. Default none.
        exceptions:
            internal.parser.node = The node has existed.
        '''
        if name in self.__data:
            error('component' : 'internal.parser.node',
                  'message' : f'The node "{name}" has existed.')
        self.__data[name] = MalangeObject(name, value, self, wrapper.__watch)
        return self.__data[name]

    def modify(self, name: str, value: any) -> None:
        '''
        Add an item to the data list.
        parameters:
            name: str = The name of the item.
            value: any = The starting value. Default none.
        exceptions:
            internal.parser.node = The node does not exist.
        '''
        if name not in self.__data:
            error('component' : 'internal.parser.node',
                  'message' : f'The node "{name}" does not exist.')
        self.__data[name].value(name)

    def remove(self, name: str) -> None:
        '''
        Remove an item.
        parameters:
            name: str = The name of the item.
        exceptions:
            internal.parser.node = The node does not exist.
        '''
        try:
            self.__data.pop(name)
        except KeyError:
            error('component' : 'internal.parser.node',
                  'message' : f'The node "{name}" does not exist.')

    def goup(self) -> MalangeNode:
        '''
        Go to the parent node.
        returns:
        1: MalangeNode = The parent node.
        '''
        return self.__parent
    def isroot(self) -> bool:
        '''
        Check if the parent root exists, if not this node is a root node.
        returns:
        1: bool = True if it is root False if it is not.
        '''
        if self.__parent == None:
            return True
        else:
            return False

class MalangeTree:
    '''
    Wrapper class to manage Malange nodes and objects.
    The idea is to save the pointer (the node) and the value object.
    This will be useful when nesting.
    - When creating a new node, the node can be 'told' who is its parents.
    - If not told the node will assume that it is a root node (the uppermost node).
    - The methods add, modify, and remove is simply wrappers. But for add,
    It returns the created MalangeObject. The add method is also given this instance
    so that the MalangeObject obtains __watch method of this instance.
    - During the creation of a MalangeObject inside MalangeNode, not only __watch
    method is given, the instance of that MalangeNode is also given so that the MalangObject
    knows its parent node.
    - When nesting, the MalangeObject (the value) will send the parent node
    via __watch to this instance of the MalangeTree to replace the pointer with
    the new Malange Node. The MalangeObject will also set its value to the instance
    of the new MalangeNode that is also notified that its parent node is the same as the parent node
    of the MalangeObject.
    - 
    '''
    def __init__(self) -> None:
        self.pointer = MalangeNode()
        self.value = None
    def add(self, name: str, value: any = None)
        self.value = self.pointer.add(name, self, value)
        return self.value
    def modify(self, name: str: value: any):
        self.pointer.modify(name)
    def remove(self, name: str):
        self.pointer.remove(name)
    def goup(self):
        parent_tree = self.pointer.goup()
        self.pointer = parent_tree # Replace the current tree with the parent tree.
    def __watch(self, new_nest: MalangeNode):
        self.pointer = new_nest # This is so that the wrapper knows the update to the nest.

class MalangeParser:
    '''
    Parser class for Malange-HTML files (.mala files)
    '''

    def __init__(self, tokens: list[Token], file: str, title: str) -> None:
    '''
    Construct the AST/CST/parse tree.

    parameters:
        tokens: Token = The tokens.
    '''
        global error
        error.register(file, title)
        self.__node = MalangeNode()
        self.__create_tree(tokens)

    def __call__(self) -> None:
    '''Print the entire AST.'''
        self.__node()

    def __load_python(self, string: str) -> None:
    '''
    Parse python objects.

    parameters:
        string: str = The python object in the form of a string.
    '''

    def __parse_attr_mala(self, attr: Token, parse: str) -> None:
    '''
    Parse attributes of a Malange block.
    
    parameters:
        attr:  str = The parsing attributes.
        parse: str = The parsing method.
    exceptions:
        syntax.malange.invalidattr = Invalid attribute format.
    '''
        global error
        err = lambda x : error({'component' : 'syntax.malange.invalidattr',
        'message' : f'Invalid attribute format for "{x}" block. See docs for more info.',
                   'index' : attr.ind})
        parsed_attr: dict[str, str] = {}

        if parse == 'for':
            words: list[str] = attr.value.split(' in ')
            if len(words) = 2:
                self.__node.add('target_list').value(
                    process_python(words[0], 'var'))
                self.__node.add('iterables').value(
                    process_python(words[1], 'mixed'))
            else:
                err('for')
        elif parse in ('while', 'if', 'elif'):
            self.__node.add('expression').value(
                process_python(attr, 'expre'))
        elif parse in ('default', 'else'):
            err(parse)
        elif parse == 'case':
            self.__node.add('value').value(process_python(attr, 'const'))
        elif parse == 'script':
            continue

    def __parse_attr_html(self, attr: Token, parse: str) -> None:
    '''
    Parse attributes of a HTML element.
    
    parameters:
        attr:  str = The parsing attributes.
    exceptions:
        syntax.malange.invalidattr = Invalid attribute format.
    '''
        global error
        err = lambda x : error({'component' : 'syntax.malange.invalidattr',
        'message' : f'Invalid attribute format for "{x}" element. See docs for more info.',
                   'index' : attr.ind})
        parsed_attr: dict[str, tuple[Union[python_object, str], str]] = {} # Parsed attributes.
        attr_list: list[str] = attr.value.split() # List of attributes.

        for attr in attr_list:
            seperated_attr: list[str] = attr.split('=') # Seperate it eg 'a=b' into 'a', 'b'
            special: str = "generic" # generic = Generic attributes. event = Event handling. bind = Variable binding.
            injecting: bool = False

            if len(seperated_attr) == 2: # means a=b which is valid

                # Check for special characters in the PROPERTY
                proper = seperated_attr[0].lstrip().rstrip()
                if re.search(r'[\?#\}\{!%^&\*\(\)\-\+~`:"\'?><|\]\[\\/;]', proper):
                    error('component' : 'syntax.malange.invalidattr',
                            'message' : ('invalid property. Characters not to be used: '
                                         '?,, !, %, ^, &, *, (, ), -, +, <, >, ?, /, \, ~, '
                                         'and `. See docs for more info.'),
                          'index' : attr.ind)
                if proper[0] == "@":
                    if '@' in proper[0:] or '$' in proper[0:]:
                        error('component' : 'syntax.malange.invalidattr',
                        'message' : (f'Invalid property {seperated_attr[0]}. '
                                     '@ and $ is used at the beginning once only. '
                                     'See docs for more info.'),
                        'index' : attr.ind)
                    else:
                        special = "event"
                elif proper[0] == "$":
                    if '@' in proper[0:] or '$' in proper[0:]:
                        error('component' : 'syntax.malange.invalidattr',
                        'message' : (f'Invalid property {seperated_attr[0]}. '
                                     '@ and $ is used at the beginning once only. '
                                     'See docs for more info.'),
                        'index' : attr.ind)
                    else:
                        special = "bind"
              
                # Now check for irregularities in the VALUE
                value = seperated_attr[1].lstrip().rstrip()
                if value.startswith('${'):
                    if value[-1] == '}':
                        python_injection = process_python(value.lstrip('${').rstrip('}'))
                        injecting = True
                    else:
                        error('component' : 'syntax.malange.invalidattr',
                              'message' : (f'Invalid value {seperated_attr[1]} of '
                                           f'property {seperated_attr[0]}. Missing } '
                                           'when attempting to inject. See docs for more info.'),
                              'index' : attr.ind)
                else:
                    if re.search(r'[\?#\}\{!%^&\*\(\)\-\+~`:"\'?><|\]\[\\/;]', proper):
                        error('component' : 'syntax.malange.invalidattr',
                              'message' : (f'Invalid value {seperated_attr[1]} '
                                           f'of property {seperated_attr[0]}. '
                                           'Special characters are dollar sign and '
                                           'curly brackets for injecting only. See docs for more info.'),
                              'index' : attr.ind

                parsed_attr[property] = (value, special) # Add it.

            else: # Means like this a=b=c or just a which is invalid of course.
                err(parse)
            
            self.__node.add('attr').value(parsed_attr)

    def __create_tree(tokens: list[Token]) -> None:
    '''
    Create the tree.
    
    parameters:
        tokens: Token = The tokens.
    exceptions:
        syntax.malange.invalidpairing = Invalid pairing eg missing > or ]
        syntax.malange.missingpairing = A block or an element is not closed.
    '''

    # The hierarchy for nesting. Usage:
    # assuming this structure:
    # <a>
    #   <p>
    #       [p][/p]
    #   </p>
    # </a>
    # <b>
    # </b>
    # the nest hierarchy will track expected closing pairs
    # to ensure proper nesting:
    # a - html
    # a - html, p - html
    # a - html, p - html, p - malange
    # a - html, p - html
    # a - html
    # none
    # b - html
    # none                 # malange/html, name, index
    nest_hierarchy: list[tuple[str, str, int]] = []

    for i, t in enumerate(tokens):

        # Get the next token.
        try:
            nt = tokens[i+1]
        except IndexError:
            nt = Token()
        # Get the double next token.
        try:
            dnt = tokens[i+2]
        except IndexError:
            dnt = Token()
        # Get the triple next token.
        try:
            tnt = tokens[i+3]
        except IndexError:
            tnt = Token()

        # Get the previous token.
        if i-1 < 0:
            pt = Token()
        else:
            pt = tokens[i-1]

        inside_block_pairing: bool = False
        inside_ele_pairing:   bool = False
        
        # Scan for opening pair of Malange block.
        if t.token == "MALANGE_BRAC_OPEN":
            self.__node.add(f'block-{nt.value}').nest()
            # Since the next token WILL BE a keyword,
            # we don't need to scan whether the next token
            # type is MALANGE_BLOCK_KEYWORD or not.
            self.__node.add('attr').nest()
            attr = self.__parse_attr_mala(dnt.value, nt.value)
            self.__node.goup()
            self.__node.add('body').nest()
            # Check if > does exist.
            if tnt.token != "MALANGE_BRAC_CLOSE":
                error({'component' : 'syntax.malange.invalidpairing', 'message' :
                    'Invalid Malange opening pair: Missing "]". See docs for more info.',
                       'index' : tnt.ind})
            nest_hierarchy.append(('malange', nt.value, t.ind))
            inside_block_pairing = True
        elif t.token == "HTML_TAG_OPEN":
            # Since the next token WILL BE a keyword,
            # we don't need to scan whether the next token
            # type is MALANGE_BLOCK_KEYWORD or not.
            self.__node.add('attr').nest()
            attr = self.__parse_attr_html(dnt.value)
            self.__node.goup()
            self.__node.add('body').nest()
            # Check if > does exist.
            if tnt.token != "HTML_TAG_CLOSE":
                error({'component' : 'syntax.malange.invalidpairing', 'message' :
                       'Invalid HTML opening pair: Missing ">". See docs for more info.',
                       'index' : tnt.ind})
            nest_hierarchy.append(('html', nt.value))
            inside_ele_pairing = True
        elif t.token == "MALANGE_BRAC_MID":
            # Check if > does exist.
            if dnt.token != "MALANGE_BRAC_CLOSE":
                error({'component' : 'syntax.malange.invalidpairing', 'message' :
                       'Invalid Malange closing pair: Missing "]". See docs for more info.',
                       'index' : dnt.ind})
            # This indicates closing.
            if nt.value == nest_hierarchy[-1][1] and nest_hierarchy[-1][0] == 'malange':
                nest_hierarchy.pop()
                self.__node.goup() # The pointer go up two times.
                self.__node.goup() # First from the body to the block, then up to the higher lev.
            # Throw error.
            else:
                error({'component' : 'syntax.malange.missingpairing',
                       'message' : (f'Missing Malange block closing pair.'
                                    f' Required keyword: "{nest_hierarchy[-1][1]}", '
                                    f'index of the opening pair: "{nest_hierarchy[-1][2]}". '
                                    'See docs for more info.'),
                       'index' : t.ind})
            inside_block_pairing = True
        elif t.token == "HTML_TAG_MID":
            # Check if > does exist.
            if dnt.token != "HTML_TAG_CLOSE":
                error({'message' : 'Invalid HTML closing pair: Missing ">"',
                       'index' : dnt.ind})
            # This indicates closing.
            if nt.value == nest_hierarchy[-1][1] and nest_hierarchy[-1][0] == 'html':
                nest_hierarchy.pop()
                self.__node.goup() # The pointer go up two times.
                self.__node.goup() # First from the body to the block, then up to the higher lev.
            # Throw error.
            else:
                error({'component' : 'syntax.malange.missingpairing',
                       'message' : (f'Missing Malange block closing pair. '
                                   f'Required keyword: "{nest_hierarchy[-1][1]}", '
                                   f'index of the opening pair: "{nest_hierarchy[-1][2]}". '
                                   'See docs for more info.'),
                       'index' : t.ind})
            inside_ele_pairing = True
        elif t.token == "HTML_JS_SCRIPT":
            self.__node.add('js_script', t.value)
        elif t.token == "PLAIN_TEXT":
            self.__node.add('plain_text', t.value)
        elif t.token == "MALANGE_BRAC_CLOSE":
            if not inside_block_pairing:
                error({'component' : 'syntax.malange.invalidpairing', 'message' :
                       'Invalid Malange closing pair: Missing "[" or "[/". See docs for more info.',
                       'index' : t.ind})
            else:
                inside_block_pairing = False
        elif t.token == "HTML_TAG_CLOSE":
            if not inside_ele_pairing:
                error({'component' : 'syntax.malange.invalidpairing', 'message' :
                       'Invalid Malange closing pair: Missing "<" or "</". See docs for more info.',
                       'index' : t.ind}) 
            else:
                inside_ele_pairing = False
        else:
            continue
            
