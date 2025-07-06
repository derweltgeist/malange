'''

    malange.internal.transpiler.tokenizer.malapyt

    malapyt = Malange Python Tokenizer

    Manages the tokenization of Malange custom Python language.
    There will be modes for tokenization.

    First one is mode 'default', aka your typical mode. All special chars
    will be detected. Second one is string, which means all characters are
    ignored except the quotes. The third one is comment, where all characters
    are ignored.

    These are the list of tokens:

    - MALANGE_BRAC_MID      [/ # Required to detect the ending script tag.

    - PYTHON_WS_GEN         Generic whitespace: space and tab.
    - PYTHON_WS_NL          cr ln ln cr # Any kind of new line.

    - PYTHON_MARK_CURVL     (    PYTHON_MARK_CURVR     )    
    - PYTHON_MARK_SQURL     [    PYTHON_MARK_SQURR     ]
    - PYTHON_MARK_CURLL     {    PYTHON_MARK_CURLR     }
    - PYTHON_MARK_DOT       .    PYTHON_MARK_COMMA     ,
    - PYTHON_MARK_COLON     :    PYTHON_MARK_SCOLON    ;
    - PYTHON_MARK_DCOLON    ::

    - PYTHON_OP_PLUS        +    PYTHON_OP_MINUS       -
    - PYTHON_OP_STAR        *    PYTHON_OP_SLASH       /
    - PYTHON_OP_DTAR        **   PYTHON_OP_DSLASH      //
    - PYTHON_OP_TILDE       ~    PYTHON_OP_CARET       ^
    - PYTHON_OP_AMPSAND     &    PYTHON_OP_GRAVE       `
    - PYTHON_OP_SLEFT       <<   PYTHON_OP_SRIGHT      >>
    - PYTHON_OP_PERCENT     %
       
    - PYTHON_AS_PLUS        +=   PYTHON_AS_MINUS       -=
    - PYTHON_AS_STAR        *=   PYTHON_AS_SLASH       /=
    - PYTHON_AS_DTAR        **=  PYTHON_AS_DSLASH      //=
    - PYTHON_AS_TILDE       ~=   PYTHON_AS_CARET       ^=
    - PYTHON_AS_AMPSAND     &=   PYTHON_AS_GRAVE       `=
    - PYTHON_AS_SLEFT       <<=  PYTHON_AS_SRIGHT      >>=
    - PYTHON_AS_DEFINE      =    PYTHON_AS_PERCENT     %=

    - PYTHON_CP_EQUAL       ==   PYTHON_CP_NOEQUAL     !=
    - PYTHON_CP_LESSEQ      <=   PYTHON_CP_MOREEQ      >=
    - PYTHON_CP_LESS        <    PYTHON_CP_MORE        >

    - PYTHON_SPEC_QUOT      " '
    - PYTHON_SPEC_DOCSTR    """, etc
    - PYTHON_SPEC_CONT      /
    
    - PYTHON_GEN_LITERAL    2323, DFDF, dfdsfs, fun_name, var_name, anything
    - PYTHON_GEN_REACTIVE   $
    - PYTHON_GEN_ARROW      ->
    - PYTHON_GEN_DECOR      @
    - PYTHON_GEN_PIPE       |
    - PYTHON_GEN_STRING     ...

    List of modifications that make PyMalange different:
    - The usage of $ to indicate reactivity: $name = ...
    - The usage of new keyword react to run functions after a variable's value change eg
      react var1 : func1(), func2() :: var2 : func2(), func3()

'''

from typing import Optional, Union

from .token import PyMalangeToken as Token

def pymalange_tokenize(string: str, infile: bool, sind: int = 0) -> Union[list[Token], int]:
    '''
    Tokenize a custom version of Malange. During tokenization/lexing several mode of
    tokenization exists. The first one is default mode, where all tokens are detected.
    The next one is string mode, where only string tokens are detected (and there is a
    nesting system which I will explain later). The third one is comment, where only
    newline tokens are detected. The modes are stored in mode variable, where tokens
    variable stored processed tokens.

    During string tokenization, the function will keep track of the declared string tokens.
    For example: "abc'cfg'xyz"
    - Token " is added. Entering mode string. Remembered: "
    - abc is added into temp_string.
    - ' is added. Remembered: " and '. ' is added into temp_string.
    - cfg is added into temp_string.
    - ' is found, closing the ' pair. Now remembered is only ". ' is added into temp_string.
    - xyz is added into temp_string.
    - " is found, triggering cleanup. temp_string is converted into a string token, while "
      is now a token too.

    For mode comment, if # is discovered comment is enabled. Durig comment = True any chars
    are not recorded. When a newline is found, comment is disabled.

    For literals are whitespaces the processes are:
    - For whitespaces, whitespace is recorded into space_tab and process_space_tab is enabled.
    - If no more whitespace, space_tab data is converted into a token, process_space_tab is False.
    - Same idea for literals. This time with literals and process_literals. Note that . and any
      special chars are processed seperately, thus 234.2323 can be 234, ., and 2323.

    If infile is True, [/ must be discovered to terminate the loop and return the tokens.
    If it is False, the loop will stop on its own and the tokens are returned.

    parameters:
        string: str  = The file string.
        infile: bool         = infile means the script is inside a .mala file.
    returns:
        1:      list[Token]  = Tokens.
        2:      int          = The last index before [.
    '''

    # The token stores.
    tokens:            list[Token]      = []
    # Available modes: default, string, and comment
    mode:              str              = "default"
    # Whitespace processing..
    process_space_tab: bool             = True
    space_tab:         str              = ""
    space_tab_start:   int              = -1
    # Literals processing.
    process_literals:  bool             = True
    literals:          str              = ""
    literals_start:    int              = -1
    # String processing.
    open_string:       list[str]        = [] # sq, dq, sq-docstring, dq-docstring
    temp_string:       str              = ''
    temp_string_start: int              = -1

    # This is the last index of the for pointer before exiting the loop.
    last_ind:          int              = 0
    found_mblock:      bool             = False

    def clean_space_tab() -> None:
        '''
            Convert space_tab into a token.
        '''
        nonlocal process_space_tab, space_tab, tokens, space_tab_start
        tokens.append(Token('PYTHON_WS_GEN', space_tab, sind+space_tab_start))
        process_space_tab = False ; space_tab_start = -1 ; space_tab = ""
    
    def clean_literals() -> None:
        '''
            Convert a literal into a token.
        '''
        nonlocal process_literals, tokens, literals_start
        tokens.append(Token('PYTHON_GEN_LITERAL', literals, sind+literals_start))
        process_literals: bool = False ; literals_start = -1 ; literals = ""

    def clean_strings() -> None:
        '''
            Convert a string into a token.
        '''
        nonlocal temp_string, tokens, temp_string_start
        tokens.append(Token('PYTHON_GEN_STRING',
                            temp_string, sind+temp_string_start))
        temp_string = "" ; temp_string_start = -1

    for ind, char in enumerate(string):

        # pchar = Previous char, dpchar = double previous, get it.
        if ind - 1 < 0:
            pchar: Optional[str] = None
        else:
            pchar: Optional[str] = string[ind-1]
        if ind - 2 < 0:
            dpchar: Optional[str] = None
        else:
            dpchar: Optional[str] = string[ind-2]
        try:
            nchar: Optional[str] = string[ind+1]
        except IndexError:
            nchar: Optional[str] = None
        try:
            dnchar: Optional[str] = string[ind+2]
        except IndexError:
            dnchar: Optional[str] = None


        ##### WS GROUP: \n, \r\n, \r, generic whitespace

        # GEN: Check for whitespace.
        if char.isspace() and char not in ('\n', '\r') and mode == "default":
            process_space_tab = True
            space_tab_start = ind
            if process_literals:
                clean_literals()
            space_tab = space_tab + char
        # NL: Check for newline.
        elif char in ('\n', '\r'):
            if mode == "comment": # Reset comment mode.
                mode = "default"
            elif mode == "string": # Pack the string, doesn't matter if it is closed or not.
                clean_strings()
            else: # That means default mode, continue.
                pass
            # UNIX-style EOL
            if char == '\n' and pchar != '\r':
                tokens.append(Token('PYTHON_WS_NL', '\\n', sind+ind))
            # MACOS-style EOL
            elif char == '\r' and nchar != '\n':
                tokens.append(Token('PYTHON_WS_NL', '\\r', sind+ind))
            # Windows-style EOL
            elif char == '\n' and pchar == '\r':
                tokens.append(Token('PYTHON_WS_NL', '\\r\\n', sind+ind))

        ##### SPEC GROUP: strings, comments, backslash, etc.

        # Backslash continuation. 
        elif char == "\\" and mode == "default":
            tokens.append(Token('PYTHON_SPEC_CONT', '\\', sind+ind))

        # Begin comment.
        elif char == "#":
            mode = "comment"

        # FOR STRINGS.
        elif char in ("'", '"') and mode != "comment":
            # If mode == default, enter string mode.
            if mode == "default":
                if char == "'" and nchar == "'" and pchar == "'": # sq-docstring
                    open_string.append('sq-docstring')
                    tokens.append(Token('PYTHON_SPEC_DOCSTR', "'''", sind+ind))
                    temp_string_start = ind+1
                elif char == '"' and nchar == '"' and pchar == '"': # dq-docstring
                    open_string.append('dq-docstring')
                    tokens.append(Token('PYTHON_SPEC_DOCSTR', '""', sind+ind-1))
                    temp_string_start = ind+1
                elif char == "'" and nchar != "'" and pchar != "'": # single-quote
                    open_string.append('sq')
                    tokens.append(Token('PYTHON_SPEC_QUOT', "'", sind+ind))
                    temp_string_start = ind+2
                elif char == '"' and nchar != '"' and pchar != '"': # double-quote
                    open_string.append("dq")
                    tokens.append(Token('PYTHON_SPEC_QUOT', '"', sind+ind-1))
                    temp_string_start = ind+2
                mode = "string"
            # Try to close the string.
            elif mode == "string":
                # Get the closing string.
                if char == "'" and nchar == "'" and pchar == "'": # sq-docstring
                    close_string: str = "sq-docstring"
                elif char == '"' and nchar == '"' and pchar == '"': # dq-docstring
                    close_string: str = "dq-docstring"
                elif char == "'" and pchar != "'" and nchar != "'": # single-quote
                    close_string: str = "sq"
                elif char == '"' and pchar != '"' and nchar != '"': # double-quote
                    close_string: str = "dq"
                # Close the string.
                if open_string[-1] == close_string:
                    open_string.pop() # Remove the last remembered string.
                    if open_string: # Remove the token from the remembered tokens list.
                        temp_string += char
                    else: # Indicating no more items, thus the cleanup of string.
                        clean_strings()
                        correct = {
                            'sq'           : ("'",   'PYTHON_SPEC_QUOT', sind+ind),
                            'dq'           : ('"',   'PYTHON_SPEC_QUOT', sind+ind),
                            'sq-docstring' : ("'''", 'PYTHON_SPEC_DOCSTR', sind+ind-1),
                            'dq-docstring' : ('"""', 'PYTHON_SPEC_DOCSTR', sind+ind-1)
                        }
                        tokens.append(
                            Token(correct[close_string][1],
                                  correct[close_string][0], correct[close_string][2]))
                # But if it doesn't match up, assume the string continues.
                else:
                    correct = {
                        "'"   : 'sq',
                        '"'   : 'dq',
                        "'''" : 'sq-docstring',
                        '"""' : 'dq-docstring'
                    }
                    temp_string += char
                    open_string.append(correct[char])
            else:
                pass

        ##### MARK GROUP: [, ], (, ), {, }, ., ,, :, ;, AND [/ DETECTION

        # All brackets, semicolon, dot, and comma.
        elif char in ('[', ']', '(', ')', '{',
                      '}', '.', ',', ';') and mode == "default":
            # INDICATES END OF THE SCRIPT
            if char == "[" and nchar == "/" and infile:
                last_ind = ind - 1
                found_mblock = True
                break
            char_name_list: Dict[str, str] = {
                '[' : 'PYTHON_MARK_SQURL',
                ']' : 'PYTHON_MARK_SQURR',
                '{' : 'PYTHON_MARK_CURLL',
                '}' : 'PYTHON_MARK_CURLR',
                '(' : 'PYTHON_MARK_CURVL',
                ')' : 'PYTHON_MARK_CURVR',
                '.' : 'PYTHON_MARK_DOT',
                ',' : 'PYTHON_MARK_COMMA',
                ';' : 'PYTHON_MARK_SCOLON'
            }
            char_name: str = char_name_list[char]
            tokens.append(Token(char_name, char, sind+ind))

        elif char == ":" and pchar != ":" and mode == "default":
            if nchar == ":": # ::
                tokens.append(Token('PYTHON_MARK_DCOLON', '::', sind+ind))
            else: # :
                tokens.append(Token('PYTHON_MARK_COLON', ':', sind+ind))

        ##### OP, AS, CP GROUP: +, -, *, /, etc AND ->

        # TOKEN +, +=
        elif char == "+" and mode == "default":
            if nchar == "=": # +=
                tokens.append(Token('PYTHON_AS_PLUS', '+=', sind+ind))
            else: # +
                tokens.append(Token('PYTHON_OP_PLUS', '+', sind+ind))
        # TOKEN -, -=, ->
        elif char == "-" and mode == "default":
            if nchar == "=": # -=
                tokens.append(Token('PYTHON_AS_MINUS', '-=', sind+ind))
            elif nchar == ">": # ->
                tokens.append(Token('PYTHON_GEN_ARROW', '->', sind+ind))
            else: # -
                tokens.append(Token('PYTHON_OP_MINUS', '-', sind+ind))
        # TOKEN ~, ~=
        elif char == "~" and mode == "default":
            if nchar == "=": # ~=
                tokens.append(Token('PYTHON_AS_TILDE', '~=', sind+ind))
            else: # ~
                tokens.append(Token('PYTHON_OP_TILDE', '~', sind+ind))
        # TOKEN ^, ^=
        elif char == "^" and mode == "default":
            if nchar == "=": # ^=
                tokens.append(Token('PYTHON_AS_CARET', '^=', sind+ind))
            else: # ^
                tokens.append(Token('PYTHON_OP_CARET', '^', sind+ind))
        # TOKEN &, &=
        elif char == "&" and mode == "default":
            if nchar == "=": # &=
                tokens.append(Token('PYTHON_AS_AMPSAND', '&=', sind+ind))
            else: # &
                tokens.append(Token('PYTHON_OP_AMPSAND', '&', sind+ind))
        # TOKEN `, `=
        elif char == "`" and mode == "default":
            if nchar == "=": # `=
                tokens.append(Token('PYTHON_AS_CARET', '`=', sind+ind))
            else: # `
                tokens.append(Token('PYTHON_OP_CARET', '`', sind+ind))
        # TOKEN %, %=
        elif char == "%" and mode == "default":
            if nchar == "=": # %=
                tokens.append(Token('PYTHON_AS_PERCENT', '%=', sind+ind))
            else: # %
                tokens.append(Token('PYTHON_OP_PERCENT', '%', sind+ind))
        # TOKEN *, **, *=, **=
        elif char == "*" and mode == "default":
            if nchar == "=": # *=
                tokens.append(Token('PYTHON_AS_STAR', '*=', sind+ind))
            elif nchar == "*" and dnchar == "=": # **=
                tokens.append(Token('PYTHON_AS_DSTAR', '**=', sind+ind))
            elif nchar == "*": # **
                tokens.append(Token('PYTHON_OP_DSTAR', '**', sind+ind))
            elif pchar == "*": # skip **
                continue
            else: # *
                tokens.append(Token('PYTHON_OP_STAR', '*', sind+ind))
        # TOKEN /, //, /=, //=
        elif char == "/" and mode == "default":
            if nchar == "=": # /=
                tokens.append(Token('PYTHON_AS_SLASH', '/=', sind+ind))
            elif nchar == "/" and dnchar == "=": # /==
                tokens.append(Token('PYTHON_AS_DSLASH', '//=', sind+ind))
            elif nchar == "/": # //
                tokens.append(Token('PYTHON_OP_DSLASH', '//', sind+ind))
            elif pchar == "/": # skip //
                continue
            else: # /
                tokens.append(Token('PYTHON_OP_SLASH', '/', sind+ind))
        # TOKEN <, <<, <=, <<=
        elif char == "<" and mode == "default":
            if nchar == "=": # <=
                tokens.append(Token('PYTHON_CP_LESSEQ', '<=', sind+ind))
            elif nchar == "<" and dnchar == "=": # <<=
                tokens.append(Token('PYTHON_AS_SLEFT', '<<=', sind+ind))
            elif nchar == "<": # <<
                tokens.append(Token('PYTHON_OP_SLEFT', '<<', sind+ind))
            elif pchar == "<": # skip <<
                continue
            else: # <
                tokens.append(Token('PYTHON_CP_LESS', '<', sind+ind))
        # TOKEN >, >>, >=, >>=
        elif char == ">" and mode == "default":
            if pchar == "-": # skip ->
                continue
            elif nchar == "=": # >=
                tokens.append(Token('PYTHON_CP_MOREEQ', '>=', sind+ind))
            elif nchar == ">" and dnchar == "=": # >>=
                tokens.append(Token('PYTHON_AS_SRIGHT', '>>=', sind+ind))
            elif nchar == ">": # >>
                tokens.append(Token('PYTHON_OP_SRIGHT', '>>', sind+ind))
            elif pchar == ">": # skip >>
                continue
            else: # >
                tokens.append(Token('PYTHON_CP_MORE', '>', sind+ind))
        # TOKEN =, !=, ==
        elif char == "=" and mode == "default":
            if pchar in ('+', '-', '*', '/', '<', '>', '~', '&', '`', '^', '%'): # skip
                continue
            elif pchar == "!": # !=
                tokens.append(Token('PYTHON_CP_NOEQUAL', '!=', sind+ind-1))
            elif pchar == "=": # ==
                tokens.append(Token('PYTHON_CP_EQUAL', '==', sind+ind-1))
            elif nchar == "=": # skip ==
                continue
            else: # =
                tokens.append(Token('PYTHON_AS_DEFINE', '=', sind+ind))

        ##### GEN GROUP: Literals, reactive, arrow, decor, pipe. EXCEPT ->

        elif char == "$" and mode == "default":
            tokens.append(Token('PYTHON_GEN_REACTIVE', '$', sind+ind))
        elif char == "@" and mode == "default":
            tokens.append(Token('PYTHON_GEN_DECOR', '@', sind+ind))
        elif char == "|" and mode == "default":
            tokens.append(Token('PYTHON_GEN_PIPE', '|', sind+ind))
        # LITERAL AND ANYTHING ELSE: Check for literals, comments, and strings.
        else:
            if mode == "default" and char.isalnum():
                process_literals = True
                if process_space_tab:
                    clean_space_tab()
                literals = literals + char
            elif mode == "comment": # For comment skip the char.
                continue
            elif mode == "string": # For string save the char to the temp_string.
                temp_string = temp_string + char

    ################################################ CLEAN UP

    if not found_mblock:
        last_ind = len(string) - 1
    
    if literals != "": # Unsaved literals are cleaned.
        clean_literals()
    elif temp_string != "": # Same with string.
        clean_strings()
    elif space_tab != "": # Ditto.
        clean_space_tab()

    return tokens, sind+last_ind

