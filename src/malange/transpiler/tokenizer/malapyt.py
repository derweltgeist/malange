'''

    malange.transpiler.tokenizer.malapyt

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

def pymalange_tokenize(string: str, infile: bool = True) -> Union[list[Token], str]:
    '''Tokenize A custom version of Malange.'''

    tokens:            list[Token]      = []
    # available modes: default, string, and comment
    mode:              str              = "default"

    # Indicating processing whitespaces.
    process_space_tab: bool             = True
    space_tab:         str              = ""

    # Indicating processing literals, aka any words/numbers/etc that are not special chars.
    process_literals:  bool             = True
    literals:          str              = ""

    # When entering string mode, the code will save the type of the string opener used.
    # It can be sq / single quote, dq / double quote, sq-docstring / ''', or dq-docstring / """
    open_string:       str              = "" # sq, dq, sq-docstring, dq-docstring
    # This is the variable used to store string data before being turned into tokens.
    temp_string:       str              = ""

    # This is the last index before exiting the loop.
    last_ind:          int              = -1

    def clean_space_tab() -> None:
        nonlocal process_space_tab, space_tab, tokens
        process_space_tab = False
        tokens.append(Token('PYTHON_WS_GEN', space_tab))
        space_tab = ""
    
    def clean_literals() -> None:
        nonlocal process_literals, tokens
        process_literals: bool = False
        tokens.append(Token('PYTHON_GEN_LITERAL', literals))
        literals = ""

    def clean_strings() -> None:
        nonlocal open_string, temp_string, tokens
        open_string = ""
        tokens.append(Token('PYTHON_GEN_STRING',
                            temp_string.strip('"').strip("'")))
        temp_string = ""

    for ind, char in enumerate(string):

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
                tokens.append(Token('PYTHON_WS_NL', '\\n'))
            # MACOS-style EOL
            elif char == '\r' and nchar != '\n':
                tokens.append(Token('PYTHON_WS_NL', '\\r'))
            # Windows-style EOL
            elif char == '\n' and pchar == '\r':
                tokens.append(Token('PYTHON_WS_NL', '\\r\\n'))

        ##### SPEC GROUP: ''', """, ", ', \, #,

        # Backslash continuation. 
        elif char == "\\" and mode == "default":
            tokens.append(Token('PYTHON_SPEC_CONT', '\\'))

        # Begin comment.
        elif char == "#":
            mode = "comment"

        # FOR STRINGS.
        elif char in ("'", '"', '"""', "'''") and mode != "comment":
            # If mode == default, enter string mode.
            if mode == "default":
                if char == "'" and nchar == "'" and pchar == "'": # sq-docstring
                    open_string = 'sq-docstring'
                    tokens.append(Token('PYTHON_SPEC_DOCSTR', "'''"))
                elif char == '"' and nchar == '"' and pchar == '"': # dq-docstring
                    open_string = 'dq-docstring'
                    tokens.append(Token('PYTHON_SPEC_DOCSTR', '""'))
                elif char == "'" and nchar != "'" and pchar != "'": # single-quote
                    open_string = 'sq'
                    tokens.append(Token('PYTHON_SPEC_QUOT', "'"))
                elif char == '"' and nchar != '"' and pchar != '"': # double-quote
                    open_string = "dq"
                    tokens.append(Token('PYTHON_SPEC_QUOT', '"'))
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
                # Close the string, go to default mode.
                if open_string == close_string:
                    clean_strings()
                    correct = {
                        'sq'           : ("'",   'PYTHON_SPEC_QUOT'),
                        'dq'           : ('"',   'PYTHON_SPEC_QUOT'),
                        'sq-docstring' : ("'''", 'PYTHON_SPEC_DOCSTR'),
                        'dq-docstring' : ('"""', 'PYTHON_SPEC_DOCSTR')
                    }
                    tokens.append(
                        Token(correct[close_string][1], correct[close_string][0]))
                # But if it doesn't match up, assume the string continues.
                else:
                    temp_string += char

        ##### MARK GROUP: [, ], (, ), {, }, ., ,, :, ;, AND [/ DETECTION

        # All brackets, semicolon, dot, and comma.
        elif char in ('[', ']', '(', ')', '{',
                      '}', '.', ',', ';') and mode == "default":
            # INDICATES END OF THE SCRIPT
            if char == "[" and nchar == "/" and infile:
                last_ind = ind
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
            tokens.append(Token(char_name, char))

        elif char == ":" and pchar != ":" and mode == "default":
            if nchar == ":":
                tokens.append(Token('PYTHON_MARK_DCOLON', '::'))
            else:
                tokens.append(Token('PYTHON_MARK_COLON', ':'))

        ##### OP, AS, CP GROUP: +, -, *, /, etc AND ->

        # TOKEN +, +=
        elif char == "+" and mode == "default":
            if nchar == "=":
                tokens.append(Token('PYTHON_AS_PLUS', '+='))
            else:
                tokens.append(Token('PYTHON_OP_PLUS', '+'))
        # TOKEN -, -=
        elif char == "-" and mode == "default":
            if nchar == "=":
                tokens.append(Token('PYTHON_AS_MINUS', '-='))
            elif nchar == ">":
                tokens.append(Token('PYTHON_GEN_ARROW', '->'))
            else:
                tokens.append(Token('PYTHON_OP_MINUS', '-'))
        # TOKEN ~, ~=
        elif char == "~" and mode == "default":
            if nchar == "=":
                tokens.append(Token('PYTHON_AS_TILDE', '~='))
            else:
                tokens.append(Token('PYTHON_OP_TILDE', '~'))
        # TOKEN ^, ^=
        elif char == "^" and mode == "default":
            if nchar == "=":
                tokens.append(Token('PYTHON_AS_CARET', '^='))
            else:
                tokens.append(Token('PYTHON_OP_CARET', '^'))
        # TOKEN &, &=
        elif char == "&" and mode == "default":
            if nchar == "=":
                tokens.append(Token('PYTHON_AS_AMPSAND', '&='))
            else:
                tokens.append(Token('PYTHON_OP_AMPSAND', '&'))
        # TOKEN `, `=
        elif char == "`" and mode == "default":
            if nchar == "=":
                tokens.append(Token('PYTHON_AS_CARET', '`='))
            else:
                tokens.append(Token('PYTHON_OP_CARET', '`'))
        # TOKEN %, %=
        elif char == "%" and mode == "default":
            if nchar == "=":
                tokens.append(Token('PYTHON_AS_PERCENT', '%='))
            else:
                tokens.append(Token('PYTHON_OP_PERCENT', '%'))
        # TOKEN *, **, *=, **=
        elif char == "*" and mode == "default":
            if nchar == "=":
                tokens.append(Token('PYTHON_AS_STAR', '*='))
            elif nchar == "*" and dnchar == "=":
                tokens.append(Token('PYTHON_AS_DSTAR', '**='))
            elif nchar == "*":
                tokens.append(Token('PYTHON_OP_DSTAR', '**'))
            elif pchar == "*":
                continue
            else:
                tokens.append(Token('PYTHON_OP_STAR', '*'))
        # TOKEN /, //, /=, //=
        elif char == "/" and mode == "default":
            if nchar == "=":
                tokens.append(Token('PYTHON_AS_SLASH', '/='))
            elif nchar == "/" and dnchar == "=":
                tokens.append(Token('PYTHON_AS_DSLASH', '//='))
            elif nchar == "/":
                tokens.append(Token('PYTHON_OP_DSLASH', '//'))
            elif pchar == "/":
                continue
            else:
                tokens.append(Token('PYTHON_OP_SLASH', '/'))
        # TOKEN <, <<, <=, <<=
        elif char == "<" and mode == "default":
            if nchar == "=":
                tokens.append(Token('PYTHON_CP_LESSEQ', '<='))
            elif nchar == "<" and dnchar == "=":
                tokens.append(Token('PYTHON_AS_SLEFT', '<<='))
            elif nchar == "<":
                tokens.append(Token('PYTHON_OP_SLEFT', '<<'))
            elif pchar == "<":
                continue
            else:
                tokens.append(Token('PYTHON_CP_LESS', '<'))
        # TOKEN >, >>, >=, >>=
        elif char == ">" and mode == "default":
            if pchar == "-":
                continue
            elif nchar == "=":
                tokens.append(Token('PYTHON_CP_MOREEQ', '>='))
            elif nchar == ">" and dnchar == "=":
                tokens.append(Token('PYTHON_AS_SRIGHT', '>>='))
            elif nchar == ">":
                tokens.append(Token('PYTHON_OP_SRIGHT', '>>'))
            elif pchar == ">":
                continue
            else:
                tokens.append(Token('PYTHON_CP_MORE', '>'))
        # TOKEN =, !=, ==
        elif char == "=" and mode == "default":
            if pchar in ('+', '-', '*', '/', '<', '>', '~', '&', '`', '^', '%'):
                continue
            elif pchar == "!":
                tokens.append(Token('PYTHON_CP_NOEQUAL', '!='))
            elif pchar == "=":
                tokens.append(Token('PYTHON_CP_EQUAL', '=='))
            elif nchar == "=":
                continue
            else:
                tokens.append(Token('PYTHON_AS_DEFINE', '='))

        ##### GEN GROUP: Literals, reactive, arrow, decor, pipe. EXCEPT ->

        elif char == "$" and mode == "default":
            tokens.append(Token('PYTHON_GEN_REACTIVE', '$'))
        elif char == "@" and mode == "default":
            tokens.append(Token('PYTHON_GEN_DECOR', '@'))
        elif char == "|" and mode == "default":
            tokens.append(Token('PYTHON_GEN_PIPE', '|'))
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

    if literals != "":
        clean_literals()
    elif temp_string != "":
        clean_strings()
    if last_ind == -1:
        cut_string: str = ""
    else:
        cut_string = string[last_ind-1:]

    return tokens, cut_string

