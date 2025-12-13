'''

    malange.internal.transpiler.tokenizer.malat

    malat = Malange Tokenizer

    Manages the tokenization of Malange blocks and HTML elements.

    The list of tokens that will be obtained are:

    - MALANGE_BRAC_OPEN     [, d
    - MALANGE_BRAC_MID      [/ d
    - MALANGE_BRAC_CLOSE    ] d
    - MALANGE_BLOCK_KEYWORD script, for, while, if, elif, else, switch, case, default d
    - MALANGE_BLOCK_ATTR    ... d
 
    - MALANGE_WRAP_OPEN     ${ d
    - MALANGE_WRAP_CLOSE    }$ d
    - MALANGE_WRAP_EXPRE    ... d

    - HTML_TAG_OPEN         < d
    - HTML_TAG_MID          </
    - HTML_TAG_CLOSE        > d
    - HTML_ELEM_KEYWORD     script, h1, etc. d
    - HTML_ELEM_ATTR        ... d
    - HTML_PLAIN_TEXT       ... d
    - HTML_JS_SCRIPT        ... d

'''

from typing import Optional

from .token import MalangeToken as Token
from .malapyt import pymalange_tokenize
from .malajst import process_js, process_style
from malange.error import ErrorManager

error = ErrorManager()

class MalangeTokenizer:
    '''Tokenizer class for each Malange file.'''

    def __init__(self, file: str, title: str) -> None:
        '''
            Initialize token, pytoken (Python tokens), style (CSS/SCSS/whatever)
            and begin lexing the file.
            parameters:
                file: str  = The file.
                title: str = The path of the file.
        '''

        global error
        error.registerfile(file, title)

        self.title:   str           = title
        self.__token:   list[Token] = []
        self.__pytoken: list[Token] = []
        self.style:   list[str]     = []
        self.__script:  bool        = False
        self.__mode:    str         = "normal" # normal, python, plain, comment
        self.__lexer(file)

    def __call__(self, mode: str = "malange") -> None:
        '''
            When called, a long list of tokens will be printed.
            Useful for debugging, so this is a debug method.
            parameters:
                mode: str = Default: malange (print Malange Tokens),
                            can be python (Python tokens).
            exceptions:
                internal.tokenizer.invalidmode = Raised when the mode args is
                                                 invalid (not python or malange).
        '''
        global error
        if mode == "malange":
            for i, t in enumerate(self.__token):
                print(f"{i} | {t()}")
        elif mode == "python":
            for i, t in enumerate(self.__pytoken):
                print(f"{i} | {t()}")
        else:
            error({'component' : 'internal.tokenizer.invalidmode', 'message' :
                f'Invalid argument "mode" value {mode} when calling MalangeTokenizer.'})

    def __lexer(self, file: str) -> None:
        '''
            The lexer that tokenizes Malange blocks and HTML elements. It of course
            scans the file char by char. There are several variables and nested funcs,
            those are there for a purpose.

            parameters:
                file:          str  = The file content string.
        '''

        ind = 0

        # Begin looping over file char by char. We use WHILE to allow us to jump iterations,
        # thus making tokenizing significantly easier.
        while ind < len(file):

            # nchar = Next character, pchar = Previous character, char = Current character
            char = file[ind]
            try:
                nchar: Optional[str] = file[ind+1]
            except IndexError:
                nchar: Optional[str] = None
            if ind - 1 < 0:
                pchar: Optional[str] = None
            else:
                pchar: Optional[str] = file[ind-1]

            # Check for Malange tags.
            if pchar != "\\" and char == "[" and self.__mode == "normal":
                new_ind = self.__process_mala_tag(file[ind+1:], ind+2)
                ind     = new_ind # Set the new index.
            # Check for HTML tags.
            elif pchar != "\\" and char == "<" and self.__mode == "normal":
                new_ind: int = self.__process_html_tag(file[ind+1:], ind+2)
                ind: int     = new_ind
            # Check for Python.
            elif self.__mode == "python":
                pass

            ind += 1
    
    def __process_mala_tag(self, file: str, sind: int) -> int:
        '''
            Created to process malange tag tokens. The mechanism is like this:
            - First it will begin by scanning whether the tag is close or not (L185).
              if yes, variable close will be enabled.
            - Second it will begin by scanning the keyword (L198). It is only done if
              check_args is not enabled. After keyword scan, the check_args is enabled.
            - Third it will scan arguments (L235, since check_args is enabled). First it will
              record the starting index of the first char of the arguments. Second any
              escaped closing bracket is recorded as part of the char without the backslash part.
              If close is enabled, raise error since arguments are only for opening tags.
            - Fourth it will finish when unescaped closing bracket is discovered.

            parameters:
                file:      str = The file string text.
                start_ind: int = The index of the '/', NOT '['
            returns:
                1:         int = The last primary index aka the primary index of unescaped ']'.
            errors:
                syntax.malange.multiplescripts       = Multiple script tags.
                syntax.malange.invalidkeyword        = Invalid keyword usage or invalid keyword.
                syntax.malange.emptykeyword          = Missing keyword.
                syntax.malange.invalidattrspacing    = Attributes are not seperated from the keywords.
                syntax.malange.invalidmalangeclosing = Invalid closing malange tags, must be: [/x]
        '''

        def peek(ind: int, string: str, file: str) -> bool:
            '''
            Peek over several characters to detect multiple chars in tokenizing
            and see if the detected chars are the same as the string args.
            Example: you have file with index 3 (provided by ind), and you want to
            peek to see if 7 characters forward are the same as "abcdefg" (provid.
            by string attr). If yes, return True. If not: return False.

            This is used to obtain keywords out of blocks and elements.

            parameters:
                ind:    int  = The index you want to start.
                string: str  = The comparison string.
                file:   str  = The file.
            returns:
                1:      bool = Indicates if it matches or not.
            '''
            length: int = len(string)
            try:
                if file[ind:ind + length] == string:
                    return True
                else:
                    return False
            except IndexError: return False

        ind:        int = 0       # Current secondary (sliced file) index.
        check_args: bool = False  # Whether the argument recording is enabled or not.
        args:       str  = ""     # String variable for arguments.
        args_begin: bool = False  # Whether argument recording has begun or not.
        args_ind:   int  = 0      # The index of the first char of the arguments.
        close:      bool = False  # Whether the tag is closed or not.
        
        while ind < len(file):
            # nchar = Next character, pchar = Previous character, char = Current character, nnchar = Double next char
            char = file[ind]
            try:
                nchar: Optional[str] = file[ind+1]
            except IndexError:
                nchar: Optional[str] = None
            try:
                pchar: Optional[str] = file[ind-1]
            except IndexError:
                pchar: Optional[str] = None
            try:
                nnchar: Optional[str] = file[ind+2]
            except IndexError:
                nnchar: Optional[str] = None

            # --- Check for [/
            keyword_list: list[str] = []
            if ind == 0:
                if char == "/":
                    self.__token.append(Token('MALANGE_BRAC_MID', '[/', sind+ind-1))
                    # Several keywords don't have a closing counterpart.
                    keyword_list = ['script', 'for', 'while', 'if', 'match']
                    close = True
                else:
                    self.__token.append(Token('MALANGE_BRAC_OPEN', '[', sind+ind-1))
                    keyword_list = ['script', 'for', 'while', 'if', 'match',
                        'elif', 'else', 'case', 'default']
            # --- Check for the keywords.
            if not check_args and char != "/":
                keyword_found: bool = False
                valid_keyword: str  = ""
                for keyword in keyword_list:
                    if peek(ind, keyword, file):
                        if keyword.isspace() or keyword == "":
                            error({
                                'component' : 'syntax.malange.emptykeyword',
                                'message'   : 'Keyword is required.',
                                'index'     : sind+ind
                            })
                        self.__token.append(Token('MALANGE_BLOCK_KEYWORD', keyword, sind+ind))
                        keyword_found = True
                        valid_keyword = keyword
                        break
                # If the keyword is 'script', enable python processing.
                if valid_keyword == "script":
                    if self.__script: # There can't be multiple [script]
                        error({
                            'component' : 'syntax.malange.multiplescripts',
                            'message'   : f'Multiple [script] tags declared, that is invalid.',
                            'index'     : sind+ind
                        })  
                    else:
                        self.__mode = "python"
                # If no keyword is found.
                if not keyword_found:
                    error({
                        'component' : 'syntax.malange.invalidkeyword',
                        'message'   : f'The utilized keywords are invalid.',
                        'index'     : sind+ind
                    })
                check_args = True
                # Skip the rest of the letters of the keywords straight to the beginning of the args.
                ind += len(valid_keyword) - 1

            # --- If keyword checking is disabled via check_args == True, add the char to the arguments.
            #     If unescaped ] is dicovered, exit tag processing.
            #     If escaped ] is discovered, add only the ] to the arguments.
            elif check_args and not close:
                if pchar != '\\' and char == '/' and nchar == ']': # If this char is discovered, end the recording of the Malange tag.
                    if args and args[0].isspace(): # The arguments must be seperated from the keyword.
                        # Append the tokens.
                        self.__token.append(Token('MALANGE_BLOCK_ATTR', args, sind+args_ind))
                        self.__token.append(Token('MALANGE_BRAC_CLOSE', ']', sind+ind))
                        break # Exit the loop.
                    else:
                        error({
                        'component' : 'syntax.malange.invalidattrspacing',
                        'message'   : f'Attribute and the keyword is not seperated by spaces.',
                        'index'     : sind+ind
                        })
                else: # Continue recording the arguments like normal.
                    # If this is the first time, args_begin will be disabled.
                    # Thus it will be enabled, then the args_ind will be recorded
                    # only once. After that the args_ind won't be touched again.
                    if not args_begin:
                        args_ind = ind
                        args_begin = True
                    # This indicates escaped brackets.
                    if char == '\\' and nchar == '/' and nnchar == ']':
                        args += '/'
                        ind += 1 # immediately jump to skip the secondary index of \.
                    # Record / 
                    elif char == '/' and nchar != ']':
                        args += char
                    else:
                        args += char # Add normal characters.
            elif check_args and close:
                if char == ']':
                    self.__token.append(Token('MALANGE_BRAC_CLOSE', ']', sind+ind))
                else:
                    error({
                        'component' : 'syntax.malange.invalidmalangeclosing',
                        'message'   : f'After a Malange keyword in a closing tag of a Malange block it must be followed by ].',
                        'index'     : sind+ind
                        })
            ind += 1
        return sind+ind

    def __process_html_tag(self, file: str, sind: int):
        '''
            Created to process html tags. The mechanism is like this:
            - First it will begin by scanning whether the tag is close or not (L185).
              if yes, variable close will be enabled.
            - Second it will begin by scanning the keyword (L198). It is only done if
              check_args is not enabled. After keyword scan, the check_args is enabled.
            - Third it will scan arguments (L235, since check_args is enabled). First it will
              record the starting index of the first char of the arguments. Second any
              escaped closing bracket is recorded as part of the char without the backslash part.
              If close is enabled, raise error since arguments are only for opening tags.
            - Fourth it will finish when unescaped closing bracket is discovered.

            parameters:
                file:      str = The file string text.
                start_ind: int = The index of the '/', NOT '['
            returns:
                1:         int = The last primary index aka the primary index of unescaped ']'.
            errors:
                syntax.html.invalidopentag     = Invalid open tag, eg '< ..' or a HTML tag containing quotes, `, <, =
                syntax.html.attronclosing      = Usage of attributes on a closing tag.
                syntax.html.invalidcharkeyword = HTML tag containing quotes, `, <, =.
        '''

        ind:           int  = 0      # Current secondary (sliced file) index.
        check_args:    bool = False  # Whether the argument recording is enabled or not.
        args:          str  = ""     # String variable for arguments.
        args_begin:    bool = False  # Whether argument recording has begun or not.
        args_ind:      int  = 0      # The index of the first char of the arguments.
        keyword:       str  = ""     # String variable for keywords.
        keyword_begin: bool = False  # Whether keyword recording has begun or not.
        keyword_ind:   int  = 0      # The index of the first char of the keywords.
        close:         bool = False  # Whether the tag is closed or not.
        
        while ind < len(file):
            # nchar = Next character, pchar = Previous character, char = Current character, nnchar = Double next char
            char = file[ind]
            try:
                nchar: str = file[ind+1]
            except IndexError:
                nchar: str = ""
            try:
                pchar: str = file[ind-1]
            except IndexError:
                pchar: str = ""
            try:
                nnchar: str = file[ind+2]
            except IndexError:
                nnchar: str = ""

            # --- Check for [/
            if ind == 0:
                if char == "/":
                    self.__token.append(Token('HTML_ELEMENT_MID', '</', sind+ind-1))
                    close = True
                    if nchar.isspace():
                        error({
                        'component' : 'syntax.html.invalidopentag',
                        'message'   : 'The "<" is seperated from the keyword.',
                        'index'     : sind+ind
                        })
                else:
                    self.__token.append(Token('HTML_ELEMENT_OPEN', '<', sind+ind-1))
                    if char.isspace():
                        error({
                        'component' : 'syntax.html.invalidopentag',
                        'message'   : 'The "<" is seperated from the keyword.',
                        'index'     : sind+ind
                        })
            # --- Check for the keywords.
            if not check_args:
                if not keyword_begin: # Again apply the same technique from Malange block args tokenization.
                    keyword_ind = ind
                    keyword_begin = True
                if char.isspace() or char in (">", "/"):
                    check_args = True # Begin checking for arguments at the next char, no more keyword scans.
                    if keyword.isspace() or keyword == "":
                        error({
                        'component' : 'syntax.html.emptykeyword',
                        'message'   : 'Keyword is required.',
                        'index'     : sind+ind
                        })
                    self.__token.append(Token('HTML_ELEMENT_KEYWORD', keyword, sind+keyword_ind))
                elif char in ("=", '"', "'", "<", "`"):
                    error({
                        'component' : 'syntax.html.invalidcharkeyword',
                        'message'   : 'The keyword can not have these characters: =, :, all quotes, `, and <.',
                        'index'     : sind+ind
                        })
                else:
                    keyword += char

            # --- If keyword checking is disabled via check_args == True, add the char to the arguments.
            #     If unescaped ] is dicovered, exit tag processing.
            #     If escaped ] is discovered, add only the ] to the arguments.
            elif check_args and not close:
                if pchar != '\\' and char == '>': # If this char is discovered, end the recording of the HTML tag.
                    # You can't insert attributes into a closing tag, so no.
                    self.__token.append(Token('MALANGE_HTML_ATTR', args, sind+args_ind))
                    self.__token.append(Token('MALANGE_HTML_CLOSE', '>', sind+ind))
                    break # Exit the loop.
                elif pchar != '\\' and char == '/' and nchar == '>':
                    self.__token.append(Token('MALANGE_HTML_ATTR', args, sind+args_ind))
                    self.__token.append(Token('MALANGE_HTML_SELFCLOSE', '/>', sind+ind))
                    ind += 1 # Skip the > since that has been taken into account.
                    break
                else: # Continue recording the arguments like normal.
                    # If this is the first time, args_begin will be disabled.
                    # Thus it will be enabled, then the args_ind will be recorded
                    # only once. After that the args_ind won't be touched again.
                    if not args_begin:
                        args_ind = ind
                        args_begin = True
                    # This indicates escaped >
                    if char == '\\' and nchar == '>':
                        args += ">"
                        ind += 1 # immediately jump to skip the secondary index of \.
                    elif char == '\\' and nchar == '/' and nnchar == '>':
                        args += "/>"
                        ind += 2 # Immediately jump to skip the secondary index of \ and /
                    else:
                        args += char # Add normal characters.
            elif check_args and close:
                if char == '>':
                    self.__token.append(Token('MALANGE_BRAC_CLOSE', '>', sind+ind))
                else:
                    error({
                        'component' : 'syntax.html.invalidhtmlclosing',
                        'message'   : f'HTML closing tag after a keyword must be followed by >.',
                        'index'     : sind+ind
                        })
            ind += 1
        return sind+ind
