'''
    malange_core.internal.engine.lexer.processor

    Serving the base template of a LexerProcessor, which serves
    as a base template class for generating lexemes from file stream.
    - Token  : Lexical unit of analysis.
    - Unit   : Divisions of a token.
    - Header : Reader of the file stream.
'''

import re
from enum import Enum
from abc import abstractmethod

NO_CONTEXT = object() # Placeholder for no no context.

def valid_unit_token(string: str) -> bool:
    '''
        Used to test if the naming is all caps snake case.

        parameter:
            string str : The text.
        return:
            bool : Indicates the text is valid or not.
    '''
    pattern = re.compile(r"^[A-Z_][A-Z0-9_]*$")
    return bool(pattern.fullmatch(string))

class LexerHeader:
    '''Header for reading the file.'''
    def __init__(self, file: str):
        '''
            Initialize the header, there should be one instance per file.

            parameter: file str : The file text.
        '''
        self.__file: str = file
        self.__ind:  str = 0
    def __call__(self) -> str:
        '''Return the current char.'''
        return self.__file[self.__ind]
    def right(self) -> None:
        '''Increase the pointer to the right by 1.'''
        if self.__ind == len(self.__file) - 1:
            exit(1) # ERROR: Pointer is beyond the right edge of the file.
        else:
            self.__ind += 1
    def left(self) -> None:
        '''Decrease the pointer to the left by 1.'''
        if self.__ind == 0:
            exit(1) # ERROR: Pointer is beyond the left edge of the file.
        else:
            self.__ind -= 1
    def slice(self, index: int, left: int = 0, right: int = 0) -> str:
        '''
            The idea is, let's say there is a Foo Bar
            I peek at 4, aka the space between the two words.
            If I tell left to be 3, it will print "Foo "
            If I tell right to be 3, it will print " Bar"
            If I tell both left and right to be 3, it will print "Foo Bar"

            parameter:
                - index int : The index of the file.
                - left  int : Take characters to the left. Default is 0.
                - right int : Take characters to the right. Default is 0.
            return:
                - str : Return the slice of the file text.
        '''
        if index - left < 0: # If the target is beyond the left edge.
            exit(1) # ERROR: Start slice is beyond the start of the file.
        if index + right + 1 > len(self.__file): # If the target is beyond the right edge.
            exit(1) # ERROR: End slice is beyond the end of the file.
        return self.__file[index-left:index+right+1]
    def peek(self, shift: int) -> str:
        '''Allows you to get a character relative to your current index'''
        if self.__ind + shift < 0:
            exit(1) # ERROR: Invalid peek shift, the target index is lower than zero.
        if self.__ind + shift > len(self.__file) - 1:
            exit(1) # ERROR: Invalid peek shift, the target index is higher than the max index.
        return self.__file[self.__ind+shift]

class LexerUnit:
    '''Composing units, aka subdivision of tokens, e.g. < ... > has < and >.'''
    def __init__(self, content: any):
        self.__content = content
    def __call__(self) -> tuple[any, int]:
        return (self.__content, self.__ind)

class LexerProcessor:
    '''Class for lexer processer, acting as the base template.'''
    def __init__(self, units: dict[str, str], tokens: dict[str, list[str]],
                 context: dict[str, list[any]], mode):
        '''
            Preparing the processor by loading the valid units, tokens, and context.
            Context indicates what modes the header must be in to detect the token.
            The context is composed like this:
            TOKEN : [ENTRY_MODE, EXIT_MODE, CONTEXT]
            - ENTRY_MODE: The mode the header must be in to detect the token.
            - EXIT_MODE : The mode the header must be in when exiting the token.
            - CONTEXT   : A callable that should be executed upon entry, set to NO_CONTEXT if no call.

            parameters:
                units   dict[str, str]       : The key is the token name, the value is the text.
                tokens  dict[str, list[str]] : The key is the token name, the list is the list of units.
                context dict[str, list[any]] : The key is the token name, the list is the CONTEXT above.
                mode                         : The list of modes.
        '''
        self.LOCK    = False # Locking system to prevent errors.
        self.UNITS   = None  # This will store enums of the units.
        self.TOKENS  = None  # This will store enums of the tokens.
        self.CONTEXT = {}    # This won't store an enum, just a map.

        # Check if the units, tokens, and context are valid.
        if units == {} or tokens == {} or context == {}:
            exit(1) # ERROR: UNITS, TOKENS, and/or CONTEXT can not be an empty dictionary.
        # Continue.
        else:

            # ----------------- Create a self.UNITS enum with self.tunits serving as temp storage.
            tunits = {} # Create a temporary container for units.
            for name, value in units.items():
                if not isinstance(name, str) or not isinstance(value, str):
                    exit(1) # ERROR: Units dictionary must follow dict[str, str]
                else:
                    if valid_unit_token(name):
                        tunits[name] = LexerUnit(value)
                    else:
                        exit(1) # ERROR: Units naming scheme is invalid!
            # Create the Units enum.
            self.UNITS = Enum("LexerUnitList", tunits)

            # ----------------- Create a self.TOKENS enum.
            ttokens = {} # Temporary containers for tokens.
            for token, value in tokens.items():
                # Check if the dictionary is valid in the first place.
                if (
                    not isinstance(token, str) or
                    not isinstance(value, list) or
                    not all(isinstance(i, str) for i in value)
                ):
                    exit(1) # ERROR: Units dictionary must follow dict[str, list[str]]
                # Continue.
                else:
                    # Check if the token name is valid.
                    if valid_unit_token(token):
                        ttokens[token] = ""
                    else:
                        exit(1) # ERROR: Token naming scheme is invalid!
                    # Check if the tuple that contains the units are valid.
                    tvalues = () # Temporary container for the tuple.
                    for unit in value:
                        try:
                            lexer_unit: LexerUnit = self.UNITS[unit]
                            tvalues.append(lexer_unit)
                        except KeyError:
                            exit(1) # ERROR: The mentioned unit in tokens dictionary does not exist.
                    ttokens[token] = tvalues
                    # Create the token enum.
                    self.TOKENS = Enum("LexerToken", ttokens)

            # ----------------- Create a self.CONTEXT map.
            for token, cont in context.items():
                # Check the actual token paired as the key.
                try:
                    actual_token = self.TOKENS[token]
                except KeyError:
                    exit(1) # ERROR: Invalid token mentioned in the contract.
                # Check the first and second items of the context: The entry and exit modes.
                try:
                    entry_mode = mode[cont[0]]
                    exit_mode  = mode[cont[1]]
                except KeyError:
                    exit(1) # ERROR: Invalid modes mentioned in the contract.
                # Check the third item of the context: The context function.
                if callable(cont[2]) or isinstance(cont[2], NO_CONTEXT):
                    self.CONTEXT[actual_token] = (entry_mode, exit_mode, cont[2])
                else:
                    exit(1) # ERROR: Invalid context function, it should be a callable or a NO_CONTEXT.
                
        # Enable the lock, indicating we are done.
        if self.LOCK == False:
            self.LOCK = True
        else:
            exit(1) # ERROR: LexerProcessor.LOCK is tempered before LexerProcessor is initialized.

    @abstractmethod
    def process(self, name: str, folder: str, header: LexerHeader):
        '''
            Used as the main logic that the child class must define, this will be executed
            everytime there is a file.

            parameters:
                name   str : The name of the file.
                folder str :
        '''
        pass
