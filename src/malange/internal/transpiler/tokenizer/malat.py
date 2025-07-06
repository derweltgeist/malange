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

    - HTML_TAG_OPEN         <, </ d
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

        self.__title:   str         = title
        self.__token:   list[Token] = []
        self.__pytoken: list[Token] = []
        self.__style:   list[str]   = []
        self.__lexer(file)

    def __call__(self, mode: str = "malange") -> None:
        '''
            When called, a long list of tokens will be printed.
            Useful for debugging, so this is a debug method.
            parameters:
                mode: str = Default: malange (print Malange Tokens),
                            can be python (Python tokens).
            exceptions:
                internal.tokenizer = Raised when the mode args is
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
            ##### --------------------------------- #####
            error({'component' : 'internal.tokenizer.invalidmode', 'message' : 
             f'Invalid argument "mode" value {mode} when calling MalangeTokenizer.'})

    def __lexer(self, file: str, script_exist: bool = False, sind: int = 0) -> None:
        '''
            The lexer that tokenizes Malange blocks and HTML elements. It of course
            scans the file char by char. There are several variables and nested funcs,
            those are there for a purpose. 
            -   when processing special chars ([, [/, <, </) it will set inside_html_tag for < and </
                to True (inside_mala_tag for [ and [/). It also set the type of the tag to type_html_tag
                and type_mala_tag. type_html_tag can be "open" (< .. <) or "close" (</ ...). Same
                with type_mala_tag. If an injection expression eg ${ ... } is encountered it will also
                set inside_brac to True. The start_brac_ind is the index for ${ for grabbing expressions
                from inside ${ ... } through slicing file. As well as start_mala_ind for Malange
                blocks and start_html_ind for HTML elements for grabbing arguments.
            -   about_to_process is used when processing '[' token. When processing '[', the
                lexer will check the keyword. If the keyword is 'script' it will set about_to_process
                and obtain the src arg of the block if it does exists to script_source and set
                script_outsourced to True if the src exists. When processing ']' it will check
                for variable inside_open_mala_block, if it is True the lexer knows the previous
                token is '[' and thus will check for the src variables. After that the text for the script
                is processed and added to self.__pytoken. Then, recursive lexing is initiated for the
                rest of the text. 
            -   script_exist is a variable that indicates that a [script] has been processed (there can't
                be multiple [script]).
            -   Same process for grabbing JS script and style script (CSS/SCSS/anything). For JS it will
                be saved in the form of tokens. While for CSS/SCSS it will be saved to self.__style
            -   When processing plain text record_ptext is set to True and plain text chars
                are added to ptext. When a special token is found the record_ptext is False &
                ptext is converted into Tokens and then set back to "". All of that are done by
                cleanup_ptext() function.
            -   When <!-- token is found, comment is enabled. If commenting is enabled the chars
                will be skipped until --> is found (thus disabling comments).
            -   process_arguments is a function to slice file string using index of [ or < and ]
                or > to obtain arguments.

            parameters:
                file:          str  = The file content string.
                script_exist:  bool = Indicates whether script block has existed or not.
                                      Optional. Default value False.
                sind:
        '''

        global error
        sind += 1

        ############# STATE/CONTROL VARIABLES

        # Can be 'default', 'python', 'js', and 'style'
        about_to_process:       str  = "default"

        # Inside tag state variables.
        inside_html_tag:        bool = False # inside < ... > or </ ... >
        inside_mala_tag:        bool = False # inside [ ... ] or [/ ... ]
        inside_brac:            bool = False # inside ${ ... }$

        # Open tag state variables (-1 = no value)
        start_brac_ind:         int  = -1 # These start_ind are for index of {
        start_html_ind:         int  = -1 # Same but for < (html element)
        start_mala_ind:         int  = -1 # Same but for [ (malange blocks)
        type_html_tag:          str  = "" # open < ... > or close </ ... >
        type_mala_tag:          str  = "" # open [ ... ] or close [/ ... ]

        # Plain text state variables.
        record_ptext:           bool = True # Recording for plain text
        ptext:                  str  = ""   # Temp variable to hold plain text

        # PyMalange state variables.
        script_outsourced:      bool = False # True if the script file is seperate
        script_source:          str  = ""    # File path if the file is seperate.
        script_exist:           bool = script_exist # Indicates there has been a [script]

        # JS state variables.
        js_outsourced:          bool = False # Same idea for PyMalange
        js_source:              str  = ""

        # Sryle state variables.
        style_outsourced:       bool = False # Ditto.
        style_source:           str  = ""

        # Comment state variables.
        comment:                bool = False # Inside <!-- .... -->

        ############ UTILITY FUNCTIONS

        def cleanup_ptext(s: List[Token]) -> None:
            '''
            Clean up plain text.

            parameters:
                s: List[Token] = The token list.
            '''
            nonlocal record_ptext, ptext
            record_ptext = False
            ptext = ""
            s.append(Token('HTML_PLAIN_TEXT', ptext, sind+ind))

        def process_arguments(s: List[Token], start_ind: int, end_ind: int,
                              tag_type: str, attr_name: str, special: str = "") -> None:
            '''
            Process args of both Malange blocks and HTML elements.

            parameters:
                s:         List[Token] = The token list.
                start_ind: int         = The index of the starting tag char [ or <
                end_ind:   int         = Same idea as start_ind for ] and >
                tag_type:  int         = open for < and [ or close for </ or [/
                attr_name: str         = The name of token. MALANGE_BLOCK_ATTR for malange
                                         and HTML_ELEM_ATTR for HTML.
                special:   str         = Optional attr. Indicates special treatment
                                         for python aka [script], js aka <script>, and
                                         and style aka <style>. Default value "".
            '''
            # If [/ has arguments obviously that is illegal so raise an error.
            if tag_type == "close":
                raise error({
                    'component' : 'syntax.malange.invalidattr',
                    'message'   : f'You have attached arguments on closing tags eg [/ or </, that is invalid.',
                    'index'     : sind+ind
                })
            # These are the variables that are involved.
            nonlocal js_source, js_outsourced, style_source, file
            nonlocal style_outsourced, script_source, script_outsourced
            global error
            # Process the arguments first.
            try:
                arguments: str = file[start_ind+1:end_ind]
            except IndexError:
                arguments: str = ""
            # For 'js', 'script', and 'style' we need to deconstruct the
            # the arguments way long before parsing to grab the src attr.
            if special in ("js", "script", "style"):
                processed_args = process_args(arguments)
                try:
                    source = processed_args['src']
                except KeyError:
                    source = ""
                if source != "":
                    if special == "js":
                        js_source = source
                        js_outsourced = True
                        s.append(Token(attr_name, arguments, sind+end_ind+1))
                    elif special == "style":
                        style_source = source
                        style_outsourced = True
                        s.append(Token(attr_name, arguments, sind+end_ind+1))
                    elif special == "script":
                        script_outsourced = True
                        script_source = stripped_args
                    else:
                        error({
                            'component' : 'internal.tokenizer.argumentprocessing',
                            'message'   : f'Invalid "special" attribute: "{special}".'
                        })
                else:
                    s.append(Token(attr_name, arguments, sind+ind))

        # Begin looping over file char by char.
        for ind, char in enumerate(file):

            # nchar = Next character, pchar = Previous character, char = Current character
            try:
                nchar: Optional[str] = file[ind+1]
            except IndexError:
                nchar: Optional[str] = None
            if ind - 1 < 0:
                pchar: Optional[str] = None
            else:
                pchar: Optional[str] = file[ind-1]

            # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>> MALANGE BLOCKS

            # ===================== Check for [ and [/
            if pchar != "\\" and char == "[" and not (
                    inside_brac or comment or inside_html_tag):

                cleanup_ptext(self.__token) # Disable plain text recording.

                # Check for [/
                if nchar == "/":
                    self.__token.append(Token('MALANGE_BRAC_MID', '[/', sind+ind))
                    # Several keywords don't have a closing counterpart.
                    keyword_list: list[str] = ['script', 'for', 'while', 'if', 'match']
                    type_mala_tag = "close"
                elif nchar != "/":
                    self.__token.append(Token('MALANGE_BRAC_OPEN', '[', sind+ind))
                    keyword_list: list[str] = ['script', 'for', 'while', 'if', 'match',
                        'elif', 'else', 'case', 'default']
                    type_mala_tag = "open"
                else: pass

                # Check for the keywords.
                keyword_found: bool = False
                for keyword in keyword_list:
                    if self.__peek(ind, keyword, file):
                        self.__token.append(Token('MALANGE_BLOCK_KEYWORD', keyword, sind+ind))
                        keyword_found = True
                        if keyword == "script":
                            if script_exist: # There can't be multiple [script]
                                error({
                                    'component' : 'syntax.malange.multiplescripts',
                                    'message'   : f'Multiple [script] tags declared, that is invalid.',
                                    'index'     : sind+ind
                                })  
                            else:
                                about_to_process = "python"
                        break
                if not keyword_found:
                    error({
                        'component' : 'syntax.malange.invalidkeyword',
                        'message'   : f'Source "{script_source}" is not found or is invalid.',
                        'index'     : sind+ind
                    })

                # Set the control vars.
                inside_mala_tag = True
                start_mala_ind = ind

            # ===================== Check for ] (also contains Python processing)
            elif pchar != r"\\" and char == "]" and not (inside_brac or comment):
                
                if not record_ptext:
                    record_ptext = True # Enable recording plain text (aka like normal)
                else:
                    error({
                                'component' : 'syntax.malange.unpairedbrac',
                                'message'   : f'] must be paired correctly.',
                                'index'     : sind+ind
                            })

                # [/ ... ] that has an argument is obviously wrong, so process_arguments
                # will raise an error, so don't worry.
                if about_to_process == "python":
                    process_arguments(self.__token,
                        start_mala_ind, ind, type_mala_tag, 'MALANGE_BLOCK_ATTR', "script")
                else:
                    process_arguments(self.__token,
                        start_mala_ind, ind, type_mala_tag, 'MALANGE_BLOCK_ATTR')

                # Add token ']' to the token list.
                self.__token.append(Token('MALANGE_BRAC_CLOSE', ']', sind+ind))

                # If about_to_process is python, we need to process the python script instead
                # of treating the python script like a Malange template code.
                if about_to_process == "python":
                    # Indicates that the script text is external and not in .mala file.
                    if script_outsourced:
                        try:
                            file = access_file(script_source)
                        except FileNotFoundError:
                            error({
                                'component' : 'file.source.invalid',
                                'message'   : f'Source "{script_source}" is not found or is invalid.',
                                'index'     : sind+start_mala_ind
                            })
                        tokens, last_ind = pymalange_tokenize(file, False) # Tokenize.
                    else:
                        # self.__process_script will return the PyTokens and the rest of the file
                        # after the Python script.
                        tokens, last_ind = pymalange_tokenize(
                            self.__file[ind+1:], True, ind+1)

                    # Clear up start_mala_ind
                    start_mala_ind = -1 ; inside_mala_tag = False

                    # Then we add the tokenized Python code to a special variable.
                    self.__pytoken = tokens
                    if script_outsourced:
                        continue # Since the Python code is seperate just assume normal.
                    else:
                        # Recursive function to tokenize the rest of the code.
                        self.__lexer(file[last_ind:], True, sind+last_ind+1)
                    break # We break the main lexing process since the recursive lexer has done the task.

            # ===================== Check for ${
            elif pchar != r"\\" and char == "$" and nchar == "{" and not (
                inside_brac or inside_mala_tag or inside_html_tag or comment):
                cleanup_ptext(self.__token)
                self.__token.append(Token('MALANGE_WRAP_OPEN', '${', sind+ind))
                start_brac_ind = ind
                inside_brac = True

            # ===================== Check for }
            elif pchar != "\\" and char == "}" and nchar == "$" and not (
                inside_html_tag or inside_mala_tag or comment or inside_brac):

                ref_object: str = file[start_brac_ind+1:ind]
                self.__token.append(Token('MALANGE_WRAP_EXPRE', ref_object, sind+ind)) # Save it.
                self.__token.append(Token('MALANGE_WRAP_CLOSE', '}', sind+ind))
                inside_brac = False
                start_brac_ind = -1
                record_ptext = True

            # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>> HTML TAGS

            # ===================== Check for <, </, and <!--
            elif pchar != '\\' and char == "<" and not (
                inside_brac or inside_mala_tag or inside_html_tag or comment):

                cleanup_ptext(self.__token)

                # Check for </
                if nchar == "/":
                    self.__token.append(Token('HTML_TAG_MID', '</', sind+ind))
                # Check for <!--, which indicates comment.
                elif nchar == "!":
                    try: third = self.__file[ind+2]
                    except IndexError: third = None
                    try: fourth = self.__file[ind+3]
                    except IndexError: fourth = None
                    if third == "-" and forth "-":
                        comment = True
                # Check for <
                else:
                    self.__token.append(Token('HTML_TAG_OPEN', '<', sind+ind))
                    inside_html_tag = True # So that the cursor will begin detecting = for attrs.

                # Check for the keywords.
                keyword: str = self.__trace_whitespace(ind, file)
                if keyword == "" or keyword.isspace():
                    raise
                start_html_ind = ind + len(keyword) # Set the open_html_ind
                ##### -------------------- #####
                elif keyword == "script": # Begin processing script blocks.
                    about_to_process = "js"
                elif keyword == "style": # Begin processing script blocks.
                    about_to_process = "style"
                self.__token.append(Token('HTML_ELEM_KEYWORD', keyword, sind+ind+1))

            # ===================== Check for >, -->, and JS-style codes.
            elif pchar != "\\" and char == ">" and not (
                inside_mala_tag or inside_brac and not comment):

                # Process -->
                if comment:
                    try: dpchar = self.__file[ind-2] # double previous char
                    except IndexError: dpchar = None
                    try: ddpchar = self.__file[ind-3] # double double previous char
                    except IndexError: ddpchar = None
                    if pchar == "-" and dpchar == "-" and ddpchar != "\\":
                        comment = False

                # If not comment.
                else:
                    record_ptext = True # Enable plain text recording.
                    # Get the arguments.
                    process_arguments(self.__token, open_html_ind, ind, 'HTML_ELEM_ATTR')
                    # Add the > token.
                    self.__token.append(Token('HTML_TAG_CLOSE', '>', sind+ind))
                    # Reset the control vars.
                    start_html_ind = -1 ; inside_html_tag = False

                    # Process js script if true.
                    if about_to_process == "js":
                        if js_outsourced:
                            f = access_file(js_source)
                            self.__tokens.append(Token('HTML_JS_SCRIPT', f, -1)) # Turned into an element.
                        else:
                            f, last_ind = process_js([ind+len("script"):])
                            self.__tokens.append(Token('HTML_JS_SCRIPT', f, -1))
                            self.__lexer(file[last_ind:], script_exist, sind+last_ind+1)
                        break # After recursive lexing we terminate the main lexing process.

                    # Process style script if true.
                    elif about_to_process == "style":
                        if style_outsourced:
                            f = access_file(style_source)
                            self.__style += f # Saved into an instance variable of the class.
                        else:
                            f, last_ind = process_style([ind+len("script"):])
                            self.__style += f
                            self.__lexer(file[last_ind:], script_exist, sind+last_ind+1)
                        break # After recursive lexing we terminate the main lexing process.

                    # If not needed just continue.
                    else:
                        pass
            
            # ===================== Record plain text, escape \ char, and escape
            # characters if in comment mode, non-ptext mode (only for a special chars
            # that are unwanted)
            else:
                special_chars: list[str] = [ # Special characters that are detected.
                    '[', ']', '<', '>', '$', '}'
                ]
                # This ensures that if \ is used to escape special characters,
                # \ is never written to the plain text.
                if char == "\\" and nchar in special_chars:
                    continue
                # For normal characters, they go into here (assuming record_ptext is true)
                elif record_ptext and not comment:
                    ptext = ptext + char
                # This is for characters that are not recorded under any mode
                # (record plain_text, inside html tags, etc)
                else:
                    continue
                    
    def __peek(self, ind: int, string: str, file: str) -> bool:
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

    def __trace_whitespace(self, ind: int, file: str) -> str:
        '''
        Peek over several characters until a whitespace is detected.
        Return the chars.

        parameters:
            ind:    int = The starting index.
            file:   str = The file string.
        returns:
            1:      str = The obtained chars.
        '''
        string: str = ""
        for i in file[ind:]:
            if i.isspace():
                return string
            else:
                string = string + i
        return string # If it is empty return it.

