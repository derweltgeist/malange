'''

    malange.internal.parser.lexer

    Manages the tokenization and lexing of Malange elements
    and HTML elements, as well as managing Python, JS, and style.

    Note that those three are not lexed, only managed to check if
    </ or [/ is in a JS/Python/style
    comments, strings, etc. No detailed full lexing.

    - JS is parsed by the browser. It won't be handled.
    - Python is parsed by the interpreter.
    - Style will be analyzed later.

    The list of tokens that will be obtained are:

    - MALANGE_TAG_OPEN           [ d
    - MALANGE_TAG_CLOSE          ] d
    - MALANGE_TAG_OPENSLASH      [/ d
    - MALANGE_TAG_CLOSESLASH     /] d
    - MALANGE_ELEMENT_KEYWORD    script, for, while, if, elif, else, switch, case, default d
    - MALANGE_ELEMENT_ATTR       ... d
    - MALANGE_ELEMENT_COMPONENT  ... d
    - MALANGE_ELEMENT_PY         ... D
    - MALANGE_ELEMENT_INJECT     { ... }

    - HTML_TAG_OPEN              < d
    - HTML_TAG_MID               </
    - HTML_TAG_CLOSE             > d
    - HTML_TAG_SELFCLOSE         /> d
    - HTML_ELEM_KEYWORD          script, h1, etc. d
    - HTML_ELEM_ATTR             ... d
    - HTML_ELEMENT_JS            ... d
    - HTML_ELEMENT_STYLE         ... d
    - HTML_ELEMENT_PLAIN         ... d

'''

from .token import MalangeToken as Token
from malange.api.error import ErrorManager

error = ErrorManager()

class Lexer:
    '''Tokenizer and lexer class for each Malange file.'''

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

        # General property variables.
        self.title:   str           = title    # Title of the file.
        self.__token:   list[Token] = []       # List of tokens.
        self.__mode:    str         = "normal" # normal, js, python, plain, comment

        # JS state variables.
        self.__js_text:        str  = ""       # js string.
        self.__js_comment:     str  = ""       # whether js scanning is entering commenting mode.
        self.__js_string:      str  = ""       # js string type (single quote or double quote or empty aka none)
        self.__js_cont_str:    bool = False    # this variable is for line continuation of single-line strings
        self.__js_ind:         int  = 0        # first index of js.

        # Python state variables.
        self.__py_exist:       bool = False    # Whether a [script/] tag has existed or not.
        self.__py_text:        str  = ""       # Python text.
        self.__py_comment:     bool = False    # whether Python scanning is entering commenting mode.
        self.__py_ind:         int  = 0        # first index of Python index.
        self.__py_cont_str:    bool = False    # Whether line continuation is true or not.

        # Python string state variables (reset when returning to normal Python mode.
        self.__py_string:      bool = False    # Indicating that Python is in string mode.
        self.__py_string_f:    bool = False    # Indicating an f-string.
        self.__py_string_r:    bool = False    # Indicating an r-string.
        self.__py_string_dq:   bool = False    # Indicating whether the string is double quote or not.
        self.__py_string_tr:   bool = False    # Indicating whether the string is triple or lone quote.

        # Style state variables.
        self.__style_text:     str  = ""
        self.__style_comment:  bool = False
        self.__style_string:   str  = ""
        self.__style_cont_str: bool = False
        self.__style_ind:      int  = 0

        # Injection (inj) and plain text state variables.
        self.__inj_ind:        int  = 0        # First index of variable injection.
        self.__inj_text:       str  = ""       # Text of the variable injection.
        self.__plain_text:     str  = ""       # To hold plain text.
        self.__plain_ind:      int  = 0        # First index of the plain text.

        self.__lexer(file)

    def __call__(self) -> list[Token]:
        '''Return the tokens.'''
        return self.__token

    def __clean_plain_txt(self):
        '''Clean plain text.'''
        self.__token.append(Token('HTML_ELEMENT_PLAIN', self.__plain_text, self.__plain_ind))
        self.__plain_text = ""
        self.__plain_ind  =  0

    def __lexer(self, file: str) -> None:
        '''
            The lexer that tokenizes Malange blocks and HTML elements. It of course
            scans the file char by char. It is context sensitive:
            - normal  : Normal mode, will collect plain text. scans for HTML comments, HTML tags, Malange tags, and var inject.
                > HTML tag parsing, which will detect for script and style keyword too.
                > Malange tag parsing, which will detect for script keyword too.
            - inject  : Variable injection.
            - comment : HTML comment.
            - python  : Lex Python. Triggered by [script/]
            - js      : Lex JS. Triggered by <script>
            - style   : Lex style. Triggered by <style>

            parameters:
                file:                         str = The file content string.
            exceptions:
                syntax.malange.multiplescript     = Multiple Malange script tag is detected.
                syntax.malange.invalidscript      = Unterminated script tag.
                syntax.malange.unterminatedpython = Same as before, but for EOF.
                syntax.html.invalidscript         = The <script> tag is not closed.
                syntax.html.unterminatedjs        = Same as before, but for EOF.
                syntax.html.invalidstyle          = <style> is not terminated.
                syntax.html.unterminatedpython    = Same as before, but for EOF.
        '''

        ind: int = 0     # Primary index.

        # Begin looping over file char by char. We use WHILE to allow us to jump iterations,
        # thus making tokenizing significantly easier.
        while ind < len(file):

            # nchar = Next character, pchar = Previous character, char = Current character
            char = file[ind]
            try:
                nchar: str = file[ind+1]
            except IndexError:
                nchar: str = ""
            try:
                nnchar: str = file[ind+2]
            except IndexError:
                nnchar: str = ""
            try:
                nnnchar: str = file[ind+3]
            except IndexError:
                nnnchar: str = ""
            if ind - 1 < 0:
                pchar: str  = ""
            else:
                pchar: str  = file[ind-1]
            if ind - 2 < 0:
                ppchar: str  = ""
            else:
                ppchar: str  = file[ind-2]
            
            # === A: Normal mode.
            if self.__mode == "normal":
                # Check for Malange tags.
                if pchar != "\\" and char == "[":
                    self.__clean_plain_txt()
                    new_ind, python = self.__process_malange_tag(file[ind+1:], ind+1)
                    ind = new_ind
                    if python:
                        if not self.__py_exist:
                            self.__py_exist = True
                            self.__mode = "python"
                            self.__py_ind = ind + 1
                        else:
                            error({
                                'component' : 'syntax.malange.multiplescript',
                        'message'   : 'There can be only one [script/].',
                        'index'     : ind  
                            })
                # Check for HTML tags.
                elif pchar != "\\" and char == "<":
                    if nchar == '!' and nnchar == '-' and nnnchar == '-':
                        self.__mode = 'comment'
                        continue
                    self.__clean_plain_txt()
                    new_ind, js, style = self.__process_html_tag(file[ind+1:], ind)
                    if js:
                        self.__mode = "js"
                        self.__js_ind = new_ind + 1
                        js = False
                    if style:
                        self.__mode = "style"
                        self.__style_ind = new_ind + 1
                    ind = new_ind
                elif pchar != "\\" and char == "{":
                    self.__clean_plain_txt()
                    self.__mode =  "inject"
                    self.__inj_ind = ind + 1
                elif char == "\\" and char in ("<", "[", "{"):
                    pass
            # === B: Inject mode.
            elif self.__mode == "inject":
                if char == '}':
                    self.__mode = 'normal'
                    self.__token.append(Token('MALANGE_ELEMENT_INJECT', self.__inj_text, self.__inj_ind))
                else:
                    self.__inj_text += char
            # === C: Comment mode.
            elif self.__mode == "comment":
                if char == "-" and nchar == "-" and nnchar == ">":
                    self.__mode = 'normal'
                    ind += 2
            # === D: Python mode.
            elif self.__mode == "python":
                if char == "[" and nchar == "/" and not self.__py_comment and not self.__py_string:
                    if not self.__py_text.isspace():
                        self.__token.append(Token('MALANGE_ELEMENT_PY', self.__py_text, self.__py_ind))
                    self.__py_text        = ""
                    self.__py_ind         = 0
                    self.__mode           = "normal"
                    self.__py_string      = False
                    self.__py_string_dq   = False
                    self.__py_string_f    = False
                    self.__py_string_r    = False
                    self.__py_string_tr   = False
                    new_ind, py    = self.__process_malange_tag(file[ind+1:], ind)
                    if not py:
                        error({
                        'component' : 'syntax.malange.invalidscript',
                        'message'   : '[script/] tag is not terminated.',
                        'index'     : ind
                        })
                    else:
                        ind = new_ind
                else:
                    jump = self.__process_py_text(char, pchar, ppchar, nchar, nnchar, ind)
                    ind += jump
            # === E: JS mode.
            elif self.__mode == "js":      
                if char == "<" and nchar == "/" and self.__js_comment == "":
                    self.__js_comment = ""
                    if not self.__js_text.isspace():
                        self.__token.append(
                            Token('HTML_ELEMENT_JS', self.__js_text, self.__js_ind))
                    self.__js_text = ""
                    self.__js_ind  = 0
                    self.__mode    = "normal"
                    new_ind, js, style = self.__process_html_tag(file[ind+1:], ind)
                    if not js:
                        error({
                        'component' : 'syntax.html.invalidscript',
                        'message'   : 'Script JS tag is not terminated.',
                        'index'     : ind
                        })
                    else:
                        ind = new_ind
                # 7-- For normal JS char, just record it normally.
                else:
                    self.__process_js_text(char, pchar, nchar, ind)
            # === F: Style mode.
            elif self.__mode == "style":      
                if char == "<" and nchar == "/" and self.__js_comment == "":
                    self.__style_comment = False
                    if not self.__style_text.isspace():
                        self.__token.append(
                            Token('HTML_ELEMENT_STYLE', self.__style_text, self.__style_ind))
                    self.__style_text = ""
                    self.__style_ind  = 0
                    self.__mode    = "normal"
                    new_ind, js, style = self.__process_html_tag(file[ind+1:], ind)
                    if not style:
                        error({
                        'component' : 'syntax.html.invalidstyle',
                        'message'   : 'Style tag is not terminated.',
                        'index'     : ind
                        })
                    else:
                        ind = new_ind
                # 7-- For normal style char, just record it normally.
                else:
                    self.__process_style_text(char, pchar, nchar, ind)
            ind += 1
        # ----- The end of file should be mode normal. -----
        if self.__mode == "js":
            error({
            'component' : 'syntax.html.unterminatedjs',
            'message'   : 'JS <script> tag is not terminated at the end of the file.',
            'index'     : ind
            })
        elif self.__mode == "python":
            error({
            'component' : 'syntax.malange.unterminatedpython',
            'message'   : 'Python [script/] tag is not terminated at the end of the file.',
            'index'     : ind
            })
        elif self.__mode == "style":
            error({
            'component' : 'syntax.html.unterminatedstyle',
            'message'   : '<style> tag is not terminated at the end of the file.',
            'index'     : ind
            })

    def __process_malange_tag(self, file: str, sind: int) -> tuple[int, bool]:
        '''
            Created to process Malange tags. The mechanism is like this:
            - First it will begin by scanning whether the tag is close or not (L185).
              if yes, variable close will be enabled.
            - Second it will begin by scanning the keyword (L198). It is only done if
              check_args is not enabled. After keyword scan, the check_args is enabled
              to ensure no keyword scanning again.
            - Third it will scan arguments (L235, since check_args is enabled). First it will
              record the starting index of the first char of the arguments. Then it began
              scanning.
                If opening tag: The scan will continue until ] of ] or / of /] is reached. 
                If closing tag: Raise error since arguments are only for begin tag. However
                if it is only whitespace it is ignored.
            - Fourth, once the chars are reached, it will exit.
            - The index is the final primary index.

            Primary index   = Index of the main loop (the __lexer loop)
            Secondary index = Index of the side loop (the __process_html_tag loop)

            parameters:
                file:                      str     = The file string text.
                start_ind:                 int     = The index of the '/', NOT '['
            returns:
                1:                         int     = The last primary index of /]
            errors:
                syntax.malange.invalidemptykeyword       = Invalid keyword in the form of just whitespace or no chars at all.
                syntax.malange.invalidcharkeyword        = Invalid keyword in the form of misusage of characters.
                syntax.malange.invalidbegintag           = Invalid begin tag, that is a misuse of else, case, and elif
                                                           as begin tags. Wrong syntax too.
                syntax.malange.invalidendtag             = Invalid end tag in the form of an end tag that contains arguments.
                syntax.malange.invalidcomponentinjection = Wrong syntax for component injection, or usage of keywords as component names.
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
        python:        bool = False  # Indicating that the variable is a JS variable.
        component:     bool = False  # Whether it is a component injection or not.
        
        # Main loop.
        while ind < len(file):
            # nchar = Next character, pchar = Previous character,
            # char = Current character, nnchar = Double next char
            char = file[ind]
            try:
                nchar: str = file[ind+1]
            except IndexError:
                nchar: str = ""
            if ind - 1 >= 0:
                pchar: str = file[ind-1]
            else:
                pchar: str = ""

            # 1-- Check for whether the opening bracket is part of a start tag (<) or end tag (</)
            if ind == 0: # On index 0m the character is either / (closing tag) or non-/ (opening tag)
                if char == "/":
                    # This means a HTML closing tag.
                    self.__token.append(Token('MALANGE_TAG_OPENSLASH', '[/', sind+ind-1))
                    close = True # Enable the close variable to True.
                    # Skip to the next char for keyword record (next block)
                    ind += 1
                    continue # Skip to the next char (the keyword).
                else:
                    self.__token.append(Token('MALANGE_TAG_OPEN', '[', sind+ind-1))

            # 2-- Check for the keywords. Since check_args default value is False, this will automatically
            # --- run after the previous if block until check_args is True. If check_args is False, this indicates
            # --- keyword checking.
            if not check_args:
                # Record the first index of the keyword. This block will only run once on the first char of the keyword.
                if not keyword_begin: # keyword_begin is written so that this block will only run once.
                    keyword_ind = ind
                    keyword_begin = True
                # This first block to detect whitespace and /] (since those two are the ender)
                # example:
                # [x attr /] -> the space between x and attr
                # [x /] -> the space between x and attr
                # [x/] -> the /]
                if char.isspace() or char == "]" or (char == "/" and nchar == "]"):
                    check_args = True # Begin checking for arguments. It can be empty, whitespace only, or filled with smth
                    if keyword.isspace() or keyword == "": # An empty or whitespace keyword is not accepted.
                        error({
                        'component' : 'syntax.malange.invalidemptykeyword',
                        'message'   : 'Keyword is required.',
                        'index'     : sind+keyword_ind
                        })
                    if keyword in ("elif", "else", "case") and close: # [elif/], [else/], and [case/]
                        error({
                        'component' : 'syntax.malange.invalidbegintag',
                        'message'   : 'Keywords elif, else, and case are only used with begin tag.',
                        'index'     : sind+keyword_ind
                        })
                    # We check if the keyword is a keyword or a component injection.
                    if keyword in ("script", "for", "while", "if", "elif", "else", "switch", "case"):
                        if keyword == "script": # After [script/] The next code is Python.
                            python = True
                            self.__token.append(Token('MALANGE_ELEMENT_KEYWORD', keyword, sind+keyword_ind))
                    else:
                        # If it is not a keyword, it must be a component injection. Which must follow this: [/x/]
                        if close: # Thus close must be True
                            component = True # When checking for closing bracket, we must ensure the closing is /] and not ]
                            self.__token.append(Token('MALANGE_ELEMENT_COMPONENT', keyword, sind+keyword_ind))
                        else:
                            error({
                            'component' : 'syntax.malange.invalidcomponentinjection',
                            'message'   : 'A component injection (NOT a keyword) must follow this syntax [/../]',
                            'index'     : sind+keyword_ind
                            })
                # Again such special characters are forbidden.
                elif char in ("=", '"', "'", "[", "`", "\\", "$", "%", "@", "#", "!", "%", "^", "&",
                              "*", "(", ")", "-", "+", ":", ";", "{", "}", "|", "<", ">", "?", "`"):
                    error({
                        'component' : 'syntax.malange.invalidcharkeyword',
                        'message'   : 'The keyword can not have these characters: =, :, all quotes, `, and <.',
                        'index'     : sind+keyword_ind
                        })
                else:
                    keyword += char # Anything other than that just add to the keyword.

            # 3-- If keyword checking is disabled via check_args == True, add the char to the arguments.
            # --- If ] or /] is dicovered, exit Malange tag scanning.
            # --- It will parse string/number/injection of a Malange argument.
            # --- This will immediately run after keyword scanning is disabled.
            if check_args and not close:
                # If ] is discovered and is not currently recording a string.
                if char == ']' and pchar != "/" and not args_str_on:
                    error({
                        'component' : 'syntax.malange.invalidbegintag',
                        'message'   : 'The format of a begin tag must be [.../]',
                        'index'     : sind+ind
                        })
                elif char == '/' and nchar == ']' and not args_str_on:
                    ind += 2
                    self.__token.append(Token('MALANGE_ELEMENT_ATTR', args, sind+args_ind))
                    self.__token.append(Token('HTML_TAG_CLOSESLASH', '/]', sind+ind))
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
                if char == ']' and pchar != "/":
                    ind += 1
                    self.__token.append(Token('MALANGE_TAG_CLOSE', ']', sind+ind))
                    break
                elif char == "/" and nchar == "]":
                    if component:
                        ind += 2
                        self.__token.append(Token('MALANGE_TAG_CLOSESLASH', '/]', sind+ind))
                    else:
                        error({
                            'component' : 'syntax.malange.invalidcomponentinjection',
    'message'   : 'A correct component injection tag is [/ .../]. Make sure you do not use keywords, make sure the brackets are right.',
                            'index'     : sind+ind
                            })
                elif char.isspace():
                    ind += 1
                    continue
                else:
                    error({
                        'component' : 'syntax.malange.invalidendtag',
    'message'   : f'A Malange end tag can not contain anything other than the brackets and the keywords.',
                        'index'     : sind+ind
                        })
            ind += 1
        return sind+ind, python

    def __process_html_tag(self, file: str, sind: int) -> tuple[int, bool, bool]:
        '''
            Created to process html tags. The mechanism is like this:
            - First it will begin by scanning whether the tag is an end tag or not.
              if yes, variable close will be enabled.
            - Second it will begin by scanning the keyword. It is only done if
              check_args is not enabled. After keyword scan, the check_args is enabled
              to ensure no keyword scanning again.
            - Third it will scan arguments (since check_args is enabled). First it will
              record the starting index of the first char of the arguments. Then it began
              scanning.
                If opening tag: The scan will continue until > of > or / of /> is reached. 
                If closing tag: Raise error since arguments are only for begin tag. However
                if it is only whitespace it is ignored.
            - Fourth, once the chars are reached (that are unescaped), it will exit.
            - The index is the final primary index.

            Primary index   = Index of the main loop (the __lexer loop)
            Secondary index = Index of the side loop (the __process_html_tag loop)

            parameters:
                file:                      str  = The file string text.
                start_ind:                 int  = The index of the '/', NOT '<'
            returns:
                1:                         int  = The last primary index of >.
            errors:
                syntax.html.invalidemptykeyword = Invalid keyword in the form of just whitespace or no chars at all.
                syntax.html.invalidcharkeyword  = Invalid keyword in the form of misusage of characters.
                syntax.html.invalidendtag       = Invalid end tag in the form of an end tag that contains arguments.
        '''

        # These are temporary state variables.
        ind:           int  = 0      # Current secondary (sliced file) ind    ex.
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
        js:            bool = False  # Whether this is a <script> tag or not.
        style:         bool = False  # Whether this is a <style> tag or not.
        
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
                        'component' : 'syntax.html.invalidemptykeyword',
                        'message'   : 'Keyword is required.',
                        'index'     : sind+keyword_ind
                        })
                    if keyword.strip() == "script":
                        js = True
                    elif keyword.strip() == "style":
                        style = True
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
                    self.__token.append(Token('HTML_ELEMENT_ATTR', args, sind+args_ind))
                    self.__token.append(Token('HTML_TAG_CLOSE', '>', sind+ind))
                    break # Exit the loop.
                elif char == '/' and nchar == '>' and not args_str_on:
                    ind += 2
                    self.__token.append(Token('HTML_ELEMENT_ATTR', args, sind+args_ind))
                    self.__token.append(Token('HTML_TAG_SELFCLOSE', '/>', sind+ind))
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
                    self.__token.append(Token('HTML_TAG_CLOSE', '>', sind+ind))
                    break
                elif char.isspace():
                    ind += 1
                    continue
                else:
                    error({
                        'component' : 'syntax.html.invalidendtag',
        'message'   : f'HTML closing tag after a keyword must be followed by >, it can be seperated by whitespace.',
                        'index'     : sind+ind
                        })
            ind += 1
        return sind+ind, js, style

    def __process_py_text(self, char: str, pchar: str, ppchar: str, nchar: str, nnchar: str, ind: int) -> int:
        '''
            Process Python text in an ugly way. The way it works is like this:
            - The modes are seperated into three types:
            > Normal: This is the default mode.
            > Commenting: Can be singleline or multiline.
            > String: Can be single-quote, double-quote, triple-single-quote, triple-double-quote.
            - Commenting is initialized with # and terminated with newline.
            - When you have a single line quote (aka triple is disabled) and you find backslash:
            > First format string must be off.
            > If it is, then recognize line continuation via self.__py_cont_str = True
            > If newline is encountered and string record is on, check if self.__py_cont_str is True,
              if it is continue and add the newline, if not throw error.
            - When a quote is detected:
            > First it will check whether it is escaped or not, raw string (self.__py_string_r) must be off.
            > Second we will check whether it will close the string or not.
            ---- IF CLOSE ----
            > It will check whether the found/closer quote is triple or lone.
                a. If yes, check if triple is ON or OFF: -> The closer quote is a triple
                    : If yes, check if the quote is the same type (Eg double or single) -> Both the closer and opener is triple
                        / If it is, close and add. -> Same type means like """ ... """ which means closing
                        / If it is not, just add. No close.
                    : If not, check if the quote is the same type. -> The opener is lone, but closer is triple
                        / If it is, error since that means " ... """ (or the single variant)
                        / If it is not, just add. No close.
                b. If not, check if the triple is ON or OFF: -> The found quote is a lone
                    : If yes, check if the quote is the same type. -> The opener is triple, but closer is lone
                        / If it is,  throw error since that means like """ ... "
                        / if it is not, just add. No close.
                    : If not, check if the quote is the same type. -> Both closer and opener is lone
                        / If it is, close and add.
                        / If it is not, just add. No close.
            ---- IF OPEN ---
            > Check if the char is single quote or double quote.
                a. If single quote pass.
                b. If double quote enable double quote.
            > Check the pchar and ppchar. Find the f/F and r/R.
                a. If f/F is found enable format string.
                b. If r/R is found enable raw string.
            > Check the nchar and nnchar.
                a. If both are the same type as char enable triple string.
                b. Append both nchar and nnchar, jump two.
            > Note that the f/F and r/R has been appended normally before a quote is found.
            ---- DETECTING [/ ----
            > For detecting [/, that is only on normal mode and is outside this function
            (in the main __lexer method)

            parameters:
                char:   str = The character of the current index.
                pchar:  str = The chracter before char.
                ppchar: str = The character before pchar.
                nchar:  str = The character after pchar.
                nnchar: str = The character after nchar.
                ind:    int = The primary index of char.
            returns:
                1:      int = Jump of primary index.
            exceptions:
                syntax.python.unterminatedstring = Invalid termination. All errors in this method use this.
        '''

        jump = 0

        # 1-- Comment detection.
        # If / is detected (and ensuring commenting and string is disabled)...
        if char == "#" and not self.__py_comment and not self.__py_string:
            self.__py_comment = True

        # 2-- If \ is detected, since this is a way you perform multiline strings for ' and "
        # e.g. like this:
        #   x = "abc \
        #   xyz"
        # this has to be taken into account. Thus js_const_str will be enabled
        # That variable if set to True means line continuation of single-line strings is True.
        elif (char == "\\" and not self.__py_comment and self.__py_string
              and not self.__py_string_tr and not self.__py_string_f):
            self.__py_cont_str = True
            self.__py_text += char

        # 3-- Newline is detected, which means...
        elif char == "\n":
            # For single line string, this means termination of string mode.
            # But if py_const_str is enabled, string mode will continue.
            if self.__py_string and not self.__py_string_tr:
                if self.__py_cont_str:
                    self.__py_cont_str = False
                    self.__py_text += char
                else:
                    error({
                        'component':'syntax.python.unterminatedstring',
            'message':'String is not terminated properly, or you try to perform line continuation without a backslash.',
                        'index':ind
                    })
            # If the comment is single line, disable the commenting mode.
            elif self.__py_comment:
                self.__py_comment = False
            else:
                self.__py_text += char

        # 4-- String detection, only if commenting is disabled.
        elif char in ('"', "'") and not self.__py_comment:
            if pchar == "\\" and ppchar !=  "\\": # Check the escape
                if self.__py_string_r: # if it is a raw string ignore the escape
                    pass
                else:
                    self.__py_text += char # The escape has been recorded the prev. loop
                    return 0
            # First we will detect whether it is closing or opening
            if self.__py_string: # Which means the closing of the string.
                # Check if the scanned char is a triple quote or not.
                if nchar == char and nnchar == char:
                    if char == '"': # We will check whether the type is the same.
                        dq = True
                    else:
                        dq = False
                    if self.__py_string_tr: # If yes, this means the closing and opening are triple
                        if dq == self.__py_string_dq: # Yes? Close.
                            self.__py_string    = False # To ensure full reset.
                            self.__py_string_dq = False
                            self.__py_string_f  = False
                            self.__py_string_r  = False
                            self.__py_string_tr = False
                        # If it does not close, no reset and continue.
                        else:
                            pass
                    else: # Indicating that the opening string is not triple.
                        if dq == self.__py_string_dq: # Aka " .... """ which is not valid
                            error({
                            'component':'syntax.python.unterminatedstring',
            'message':'String is not terminated properly, or you try to perform line continuation without a backslash.',
                            'index':ind
                            })
                        else:
                            pass
                    self.__py_text += f"{char}{nchar}{nnchar}" # Add the chars and jump by 2.
                    jump = 2
                else: # If the char is not a triple quote...
                    if char == '"': # Check the type. 
                        dq = True
                    else:
                        dq = False
                    if dq == self.__py_string_dq: # If it is the same type:
                        if self.__py_string_tr: # Basically e.g. " ... """ .., it is invalid
                            error({
                            'component':'syntax.python.unterminatedstring',
            'message':'String is not terminated properly, or you try to perform line continuation without a backslash.',
                            'index':ind
                            })
                        else: # Basically e.g. " ... " ..., which is valid
                            self.__py_string    = False # To ensure full reset.
                            self.__py_string_dq = False
                            self.__py_string_f  = False
                            self.__py_string_r  = False
                            self.__py_string_tr = False # If it does not close, it won't close.                           
                    else: # If it not the same type, just add it like normal eg """ ... ' or " ... '
                        self.__py_text += f"{char}"
            else: # Which means the opening of the string.
            # Enable self.__py_string first
                self.__py_string = True
                # Check if it is single quote or not.
                if char == '"':
                    self.__py_string_dq = True
                    self.__py_text += '"'
                elif char == "'":
                    self.__py_string_dq = False
                    self.__py_text += "'"
                # First analyze the f and r prefix.
                if pchar in ("F", "f"):
                    self.__py_string_f = True
                    if ppchar in ("R", "r"):
                        self.__py_string_r = True
                elif pchar in ("R", "r"):
                    self.__py_string_r = True
                    if ppchar in ("F", "f"):
                        self.__py_string_f = True
                # Second we will analyze whether it is a triple quote or not.
                if nchar == char and nnchar == char:
                    self.__py_string_tr = True
                    self.__py_text += f"{char}{nchar}{nnchar}" # The f/F and r/R has been recorded in the previous loop.
                    jump = 2 # We want to skip the nchar and nnchar.
        # 6-- For normal PY char, just record it normally.
        else:
            if not self.__py_comment:
                self.__py_text += char
        return jump

    def __process_js_text(self, char: str, pchar: str, nchar: str, ind: int) -> None:
        '''
            Process JS text. The way it works is like this:
            - The modes are seperated into three types:
            > Normal: This is the default mode.
            > Commenting: Can be singleline or multiline.
            > String: Can be single-quote, double-quote, or backticks.
            - The way they are treated is different:
            > For singleline commenting, it is initiated with // in normal mode
            and terminated with newline in normal mode too.
            > For multiline commenting, it is initiated with /* and terminated
            with */ in normal mode.
            > For single line string (quotes), it is initiated and terminated with the same
            quote (singlequote for singlequote) or newline. Yes, newline. Even if that is
            a syntax error, it is not the job of us to fix it.
            > For double line string (backticks), it is initiated with ` and terminated
            with ` too.
            > For detecting </, that is only on normal mode and is outside this function
            (in the main __lexer method)

            parameters:
                char:  str = The character of the current index.
                pchar: str = The chracter before char.
                nchar: str = The character after pchar.
                ind:   int = The primary index of char.
            exceptions:
                syntax.js.unterminatedstring = Inproper string termination.
        '''

        # 1-- Comment detection.
        # If / is detected (and ensuring commenting and string is disabled)...
        if char == "/" and self.__js_comment == "" and self.__js_string == "":
            if nchar == "/": # If //, this means single line commenting is on
                self.__js_comment = "sl"
            elif nchar == "*": # If /*, this means multi line commenting is on
                self.__js_comment = "ml"
            else: # If it is just /, treat it usual
                if pchar == "/":
                    pass
                else:
                    self.__js_string += char

        # 2-- If \ is detected, since this is a way you perform multiline strings for ' and "
        # e.g. like this:
        #   x = "abc \
        #   xyz"
        # this has to be taken into account. Thus js_const_str will be enabled
        # That variable if set to True means line continuation of single-line strings is True.
        elif char == "\\" and self.__js_comment == "" and self.__js_string in ("'", '"'):
            self.__js_cont_str = True
            self.__js_text += char

        # 3-- Newline is detected, which means...
        elif char == "\n":
            # For single line string, this means termination of string mode.
            # But if js_const_str is enabled, string mode will continue.
            if self.__js_string in ('"', "'"):
                if self.__js_cont_str:
                    self.__js_cont_str = False
                    self.__js_text += char
                else:
                    error({
                        'component':'syntax.js.unterminatedstring',
            'message':'String is not terminated properly, or you try to perform line continuation without a backslash.',
                        'index':ind
                    })
            # If the comment is single line, disable the commenting mode.
            elif self.__js_comment == "sl":
                self.__js_comment = ""
            else:
                self.__js_text += char

        # 4-- This means termination for multiline comment, only if string mode is off
        elif char == "*" and nchar == "/" and self.__js_comment == "ml" and self.__js_string == "":
            self.__js_comment = ""

        # 5-- String detection, only if commenting is disabled.
        elif char in ('"', "'", '`') and pchar != "\\" and self.__js_comment == "":
            if self.__js_string == "":
                self.__js_string = char # Save the type of string initializer.
            else:
                if self.__js_string == char:
                    self.__js_string = ""
            self.__js_text += char

        # 6-- For normal JS char, just record it normally.
        else:
            if self.__js_comment == "":
                self.__js_text += char

    def __process_style_text(self, char: str, pchar: str, nchar: str, ind: int) -> None:
        '''
            Process style text like JS but without single-line thing.
            SCSS and different styling will be added later.
            
            parameters:
                char:  str = The character of the current index.
                pchar: str = The chracter before char.
                nchar: str = The character after pchar.
                ind:   int = The primary index of char.
            exceptions:
                syntax.style.unterminatedstring = Inproper string termination.
        '''

        # 1-- Comment detection.
        # If / is detected (and ensuring commenting and string is disabled)...
        if char == "/" and nchar == "*" and not self.__style_comment and self.__style_string == "":
            self.__style_comment = True

        # 2-- If \ is detected, since this is a way you perform multiline strings for ' and "
        # e.g. like this:
        #   x = "abc \
        #   xyz"
        # this has to be taken into account. Thus js_const_str will be enabled
        # That variable if set to True means line continuation of single-line strings is True.
        elif char == "\\" and not self.__style_comment and self.__style_string in ("'", '"'):
            self.__style_cont_str = True
            self.__style_text += char

        # 3-- Newline is detected, which means...
        elif char == "\n":
            # For single line string, this means termination of string mode.
            # But if js_const_str is enabled, string mode will continue.
            if self.__style_string in ('"', "'"):
                if self.__style_cont_str:
                    self.__style_cont_str = False
                    self.__style_text += char
                else:
                    error({
                        'component':'syntax.style.unterminatedstring',
            'message':'String is not terminated properly, or you try to perform line continuation without a backslash.',
                        'index':ind
                    })
            else:
                self.__style_text += char

        # 4-- This means termination for multiline comment, only if string mode is off
        elif char == "*" and nchar == "/" and self.__style_comment and self.__style_string == "":
            self.__style_comment = False

        # 5-- String detection, only if commenting is disabled.
        elif char in ('"', "'", '`') and pchar != "\\" and not self.__style_comment:
            if self.__style_string == "":
                self.__style_string = char # Save the type of string initializer.
            else:
                if self.__style_string == char:
                    self.__style_string = ""
            self.__style_text += char

        # 6-- For normal JS char, just record it normally.
        else:
            if self.__style_comment == "":
                self.__style_text += char

