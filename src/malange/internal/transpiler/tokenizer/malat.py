'''

    malange.internal.transpiler.tokenizer.malat

    malat = Malange Tokenizer

    Manages the tokenization of Malange blocks and HTML elements.

    The list of tokens that will be obtained are:

    - MALANGE_BRAC_BEGINOPEN     [ d
    - MALANGE_BRAC_BEGINCLOSE    /] d
    - MALANGE_BRAC_ENDOPEN       [/ d
    - MALANGE_BRAC_ENDCLOSE      ]
    - MALANGE_BLOCK_KEYWORD      script, for, while, if, elif, else, switch, case, default d
    - MALANGE_BLOCK_ATTR         ... d
 
    - MALANGE_WRAP_OPEN          ${ d
    - MALANGE_WRAP_CLOSE         }$ d
    - MALANGE_WRAP_EXPRE         ... d

    - HTML_TAG_OPEN              < d
    - HTML_TAG_MID               </
    - HTML_TAG_CLOSE             > d
    - HTML_TAG_SELFCLOSE         /> d
    - HTML_ELEM_KEYWORD          script, h1, etc. d
    - HTML_ELEM_ATTR             ... d
    - HTML_PLAIN_TEXT            ... d
    - HTML_JS_SCRIPT             ... d

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
        js  = False

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
                new_ind, js = self.__process_mala_tag(file[ind+1:], ind+1)
                ind: int    = new_ind # Set the new index.
            # Check for HTML tags.
            elif pchar != "\\" and char == "<" and self.__mode == "normal":
                new_ind: int = self.__process_html_tag(file[ind+1:], ind)
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
                file:                            str = The file string text.
                start_ind:                       int = The index of the '/', NOT '['
            returns:
                1:                               int = The last primary index aka the primary index of unescaped ']'.
            errors:
                syntax.malange.invalidkeyword        = Invalid character inside a keyword.
                syntax.malange.emptykeyword          = Missing keyword or just whitespaces.
                syntax.malange.invalidendtag         = Invalid end tags, eg an end tag having an attr or having />
        '''

        # These are temporary state variables.
        ind:           int  = 0      # Current secondary (sliced file) index.
        # ------
        check_attr:    bool = False  # Whether the argument recording is enabled or not.
        attr:          str  = ""     # String variable for attributes.
        attr_ind:      int  = 0      # The index of the first char of the attributes.
        attr_str_on:   bool = False  # Indicating that the attribute is inside a string eg style="..."
        attr_str_char: str  = ""     # Whether the string begin quote is single or double.
        # ------
        keyword:       str  = ""     # String variable for keywords.
        keyword_begin: bool = False  # Whether keyword recording has begun or not.
        keyword_ind:   int  = 0      # The index of the first char of the keywords.
        # ------
        end:          bool = False  # Whether the tag is an end or an open tag.
        
        while ind < len(file):
            # nchar = Next character, pchar = Previous character, char = Current character, nnchar = Double next char
            char = file[ind]
            try:
                nchar: Optional[str] = file[ind+1]
            except IndexError:
                nchar: Optional[str] = None

            # --- Check for [/
            # 1-- Check for whether the opening bracket is part of a start tag (<) or end tag (</)
            if ind == 0: # On index 0m the character is either / (closing tag) or non-/ (opening tag)
                if char == "/":
                    # This means a HTML closing tag.
                    self.__token.append(Token('HTML_TAG_MID', '</', sind+ind))
                    end = True # Enable the close variable to True.
                    # Skip to the next char for keyword record (next block)
                    ind += 1
                    continue # Skip to the next char (the keyword).
                else:
                    self.__token.append(Token('HTML_TAG_OPEN', '<', sind+ind))

            # 2-- Check for the keywords. Since check_args default value is False, this will automatically
            # --- run after the previous if block until check_args is True. If check_args is False, this indicates
            # --- keyword checking.
            if not check_attr:
                # Record the first index of the keyword. This block will only run once on the first char of the keyword.
                if not keyword_begin: # keyword_begin is written so that this block will only run once.
                    keyword_ind = ind + 1
                    keyword_begin = True
                # This first block to detect whitespace, >, or /> (as those are the ones who end keyword detect)
                if char.isspace() or char == ">" or (char == "/" and nchar == ">"):
                    check_attr = True # Begin checking for arguments (or ending the HTML tag scan) at the next char.
                    if keyword.isspace() or keyword == "": # An empty or whitespace keyword is not accepted.
                        error({
                                'component' : 'syntax.html.emptykeyword',
                                'message'   : 'A keyword is required.',
                                'index'     : sind+keyword_ind
                            })
                    self.__token.append(Token('HTML_ELEMENT_KEYWORD', keyword, sind+keyword_ind))
                    attr_ind = ind + 1
                elif char in ("=", '"', "'", "<", "`", "\\"): # A keyword that contains these chars is not accepted.
                    error({
                        'component' : 'syntax.html.invalidkeyword',
                        'message'   : f'The utilized keywords are invalid, please check that no illegal chars exist.',
                        'index'     : sind+ind-1
                    })

            # 3-- If keyword checking is disabled via check_args == True, add the char to the arguments.
            # --- If > or /> is dicovered, exit HTML tag scanning.
            # --- It will parse string/number/injection of a HTML argument.
            # --- This will immediately run after keyword scanning is disabled.
            if check_attr and not end:
                # If > is discovered and is not currently recording a string.
                if char == '>' and not attr_str_on:
                    # You can't insert attributes into a closing tag, so no.
                    ind += 1
                    if attr != "":
                        self.__token.append(Token('HTML_ELEMENT_ATTR', attr, sind+attr_ind))
                    self.__token.append(Token('HTML_TAG_CLOSE', '>', sind+ind))
                    break # Exit the loop.
                elif char == '/' and nchar == '>' and not attr_str_on:
                    ind += 2
                    if attr != "":
                        self.__token.append(Token('HTML_ELEMENT_ATTR', attr, sind+attr_ind))
                    self.__token.append(Token('HTML_TAG_SELFCLOSE', '/>', sind+ind-1))
                    break
                # Continue recording the arguments like normal.
                else:
                    # This indicates escaped >
                    if char in ('"', "'"):
                        if char == attr_str_char:
                            attr_str_on = False
                            attr_str_char = ""
                        else:
                            attr_str_on = True
                            attr_str_char = char
                            attr += char
                    else:
                        attr += char # Add normal characters.
            elif check_attr and end: # Aka a closing bracket of an end tag.
                if char == '/' and nchar == '>': # /> ending for imported Malange file, NOT vanilla
                    self.__token.append(Token('HTML_TAG_CLOSE', '/>', sind+ind+1))
                elif char == '>': # > Ending for typical HTML end tag.
                    self.__token.append(Token('HTML_TAG_CLOSE', '>', sind+ind+1))
                    ind += 1
                    break
                elif char.isspace(): # space is skipped.
                    ind += 1
                    continue
                else: # No attributes are allowed.
                    error({
                        'component' : 'syntax.html.invalidendtag',
                        'message'   : f'A HTML end tag can not have attributes.',
                        'index'     : sind+ind
                        })
            ind += 1
        return sind+ind

    def __process_html_tag(self, file: str, sind: int) -> tuple[int, bool]:
        '''
            Created to process html tags. The mechanism is like this:
            - First it will begin by scanning whether the tag is close or not (L185).
              if yes, variable close will be enabled.
            - Second it will begin by scanning the keyword (L198). It is only done if
              check_args is not enabled. After keyword scan, the check_args is enabled
              to ensure no keyword scanning again.
            - Third it will scan arguments (L235, since check_args is enabled). First it will
              record the starting index of the first char of the arguments. Then it began
              scanning.
                If opening tag: The scan will continue until > of > or / of /> is reached. 
                If closing tag: Raise error since arguments are only for opening tags. However
                if it is only whitespace it is ignored.
            - Fourth, once the chars are reached (that are unescaped), it will exit.
            - The index is the final primary index.

            Primary index   = Index of the main loop (the __lexer loop)
            Secondary index = Index of the side loop (the __process_html_tag loop)

            parameters:
                file:                      str = The file string text.
                start_ind:                 int = The index of the '/', NOT '['
            returns:
                1:                         int = The last primary index aka the primary index of unescaped ']'.
            errors:
                syntax.html.invalidopentag     = Invalid open tag, eg '< ..' or a HTML tag containing quotes, `, <, =
                syntax.html.attronclosing      = Usage of attributes on a closing tag.
                syntax.html.invalidcharkeyword = HTML tag containing quotes, `, <, =.
        '''

        # These are temporary state variables.
        ind:           int  = 0      # Current secondary (sliced file) index.
        # ------
        check_args:    bool = False  # Whether the argument recording is enabled or not.
        args:          str  = ""     # String variable for arguments.
        args_begin:    bool = False  # Whether argument recording has begun or not.
        args_ind:      int  = 0      # The index of the first char of the arguments.
        args_str_on:   bool = False  # Indicating that the argument is inside a string eg style="..."
        args_str_char: str  = ""     # Whether the string begin quote is single or double.
        # ------
        keyword:       str  = ""     # String variable for keywords.
        keyword_begin: bool = False  # Whether keyword recording has begun or not.
        keyword_ind:   int  = 0      # The index of the first char of the keywords.
        # ------
        close:         bool = False  # Whether the tag is closed or not.
        js:            bool = False
        
        # Main loop.
        while ind < len(file):
            # nchar = Next character, pchar = Previous character,
            # char = Current character, nnchar = Double next char
            char = file[ind]
            try:
                nchar: str = file[ind+1]
            except IndexError:
                nchar: str = ""

            # 1-- Check for whether the opening bracket is part of a start tag (<) or end tag (</)
            if ind == 0: # On index 0m the character is either / (closing tag) or non-/ (opening tag)
                if char == "/":
                    # This means a HTML closing tag.
                    self.__token.append(Token('HTML_ELEMENT_MID', '</', sind+ind-1))
                    close = True # Enable the close variable to True.
                    # Skip to the next char for keyword record (next block)
                    ind += 1
                    continue # Skip to the next char (the keyword).
                else:
                    self.__token.append(Token('HTML_ELEMENT_OPEN', '<', sind+ind-1))

            # 2-- Check for the keywords. Since check_args default value is False, this will automatically
            # --- run after the previous if block until check_args is True. If check_args is False, this indicates
            # --- keyword checking.
            if not check_args:
                # Record the first index of the keyword. This block will only run once on the first char of the keyword.
                if not keyword_begin: # keyword_begin is written so that this block will only run once.
                    keyword_ind = ind
                    keyword_begin = True
                # This first block to detect whitespace, >, or /> (as those are the ones who end keyword detect)
                if char.isspace() or char == ">" or (char == "/" and nchar == ">"):
                    check_args = True # Begin checking for arguments (or ending the HTML tag scan) at the next char.
                    if keyword.isspace() or keyword == "": # An empty or whitespace keyword is not accepted.
                        error({
                        'component' : 'syntax.html.emptykeyword',
                        'message'   : 'Keyword is required.',
                        'index'     : sind+keyword_ind
                        })
                    if keyword == "script":
                        js = True
                    self.__token.append(Token('HTML_ELEMENT_KEYWORD', keyword, sind+keyword_ind))
                elif char in ("=", '"', "'", "<", "`", "\\"): # A keyword that contains these chars is not accepted.
                    error({
                        'component' : 'syntax.html.invalidcharkeyword',
                        'message'   : 'The keyword can not have these characters: =, :, all quotes, `, and <.',
                        'index'     : sind+keyword_ind
                        })
                else:
                    keyword += char # Anything other than that just add to the keyword.

            # 3-- If keyword checking is disabled via check_args == True, add the char to the arguments.
            # --- If > or /> is dicovered, exit HTML tag scanning.
            # --- It will parse string/number/injection of a HTML argument.
            # --- This will immediately run after keyword scanning is disabled.
            if check_args and not close:
                # If > is discovered and is not currently recording a string.
                if char == '>' and not args_str_on:
                    # You can't insert attributes into a closing tag, so no.
                    ind += 1
                    self.__token.append(Token('MALANGE_HTML_ATTR', args, sind+args_ind))
                    self.__token.append(Token('MALANGE_HTML_CLOSE', '>', sind+ind))
                    break # Exit the loop.
                elif char == '/' and nchar == '>' and not args_str_on:
                    ind += 2
                    self.__token.append(Token('MALANGE_HTML_ATTR', args, sind+args_ind))
                    self.__token.append(Token('MALANGE_HTML_SELFCLOSE', '/>', sind+ind))
                    break
                # Continue recording the arguments like normal.
                else:
                    # If this is the first time, args_begin will be disabled.
                    # Thus it will be enabled, then the args_ind will be recorded
                    # only once. After that the args_ind won't be touched again.
                    if not args_begin:
                        args_ind = ind
                        args_begin = True
                    # This indicates escaped >
                    if char in ('"', "'"):
                        if char == args_str_char:
                            args_str_on = False
                            args_str_char = ""
                        else:
                            args_str_on = True
                            args_str_char = char
                        args += char
                    else:
                        args += char # Add normal characters.
            elif check_args and close:
                if char == '>':
                    ind += 1
                    self.__token.append(Token('MALANGE_BRAC_CLOSE', '>', sind+ind))
                    break
                elif char.isspace():
                    ind += 1
                    continue
                else:
                    error({
                        'component' : 'syntax.html.invalidhtmlclosing',
        'message'   : f'HTML closing tag after a keyword must be followed by >, it can be seperated by whitespace.',
                        'index'     : sind+ind
                        })
            ind += 1
        return sind+ind, js
