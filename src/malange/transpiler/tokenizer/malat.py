'''

    malange.transpiler.tokenizer.malat

    malat = Malange Tokenizer

    Manages the tokenization of Malange blocks and HTML elements.

    The list of tokens that will be obtained are:

    - MALANGE_BRAC_OPEN     [, d
    - MALANGE_BRAC_MID      [/ d
    - MALANGE_BRAC_CLOSE    ] d
    - MALANGE_BLOCK_KEYWORD script, for, while, if, elif, else, switch, case, default d
    - MALANGE_BLOCK_ATTR    ... d
 
    - MALANGE_WRAP_OPEN     ${ d
    - MALANGE_WRAP_CLOSE    } d
    - MALANGE_WRAP_EXPRE    ... d

    - HTML_TAG_OPEN         <, </ d
    - HTML_TAG_CLOSE        > d
    - HTML_ELEM_KEYWORD     script, h1, etc. d
    - HTML_ELEM_ATTR        ... d
    - HTML_PLAIN_TEXT       ... d
    - HTML_JS_SCRIPT        ...

'''

from typing import Optional

from .token import MalangeToken as Token
from .malapyt import pymalange_tokenize
from .malajst import process_js, process_style

class MalangeTokenizer:
    '''Tokenizer class for each Malange file.'''
    def __init__(self, file: str):
        self.__token:   list[Token] = []
        self.__pytoken: list[Token] = []
        self.__style:   str         = ""
        self.__lexer(file)
    def __call__(self, mode: str = "malange"):
        if mode == "malange":
            for i, t in enumerate(self.__token):
                print(f"{i}: {t}")
        elif mode == "python":
            for i, t in enumerate(self.__pytoken):
                print(f"{i}: {t}")
        else:
            raise ##### ---------------------- #####

    def __lexer(self, file: str, script_exist: bool = False):
        '''The lexer that tokenizes Malange blocks and HTML elements.'''

        # About to process what mode. Use to pass information from processing token
        # [ to token ]. Example: If about to process [script], obviously the pointer
        # must process the Python code specially. Thus if [ (which handles the keyword)
        # determines the keyword to be == "script" it will change the about_to_process
        # to "python", then ] elif block will check if the about_to_process is "python",
        # if yes it will treat the script code as Python code. Other values: js and style.
        about_to_process: str = "default"

        # Indicates that the pointer is inside an opening HTML element eg <script>
        # Useful for lexing attributes. Same for Malange opening block and inside brackets.
        inside_open_html_ele:   bool = False
        inside_open_mala_block: bool = False
        inside_brac:            bool = False

        # Position of an open curly brackets. This is used to obtain the object referenced
        # between { and }. -1 = No index.
        open_brac_ind: int = -1
        # Same idea for processing arguments. Instead of 'type' '=' 'text/javascript'
        # my idea is just to carry the entirety eg 'type=text/javascript' and process it
        # later in the parser. And yes -1 = No index.
        open_html_ind: int = -1
        # Same idea for Malange arguments.
        open_mala_ind: int = -1

        # Recording plain text.
        record_ptext: bool = True
        ptext:        str  = ""

        # variable indicating if the script is outsourced.
        script_outsourced: bool = False
        script_source:     str  = ""
        script_exist:      bool = script_exist # Only one [script] is allowed.

        # Same for js and style
        js_outsourced:     bool = False
        js_source:         str  = ""
        style_outsourced:  bool = False
        style_source:      str  = ""

        # Is comment enabled?
        comment:           bool = False

        def cleanup_ptext(s: List[Token]) -> None:
            '''Clean up plain text.'''
            nonlocal record_ptext
            record_ptext = False
            ptext = ""
            s.append(Token('HTML_PLAIN_TEXT', ptext))

        def process_arguments(s: List[Token], start_ind: int, end_ind: int,
                              attr_name: str, special: str = "") -> None:
            '''Process args of both Malange blocks and HTML elements'''
            nonlocal js_source, js_outsourced, style_source, file
            nonlocal style_outsourced, script_source, script_outsourced
            # Process the arguments first.
            arguments = file[start_ind+1:end_ind]
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
                        s.append(Token(attr_name, arguments))
                    elif special == "style":
                        style_source = source
                        style_outsourced = True
                        s.append(Token(attr_name, arguments))
                    elif special == "script":
                        script_outsourced = True
                        script_source = stripped_args
                else:
                    s.append(Token(attr_name, arguments))

        for ind, char in enumerate(file):
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
            if pchar != r"\\" and char == "[" and not inside_brac and not comment:
                cleanup_ptext(self.__token)
                # Check for [/
                if nchar == "/":
                    self.__token.append(Token('MALANGE_BRAC_MID', '[/'))
                    # Several keywords don't have a closing counterpart.
                    keyword_list: list[str] = ['script', 'for', 'while', 'if', 'switch']
                # Check for [, to make it faster if the pointer is inside js/style/python code,
                # no processing (else: continue)
                elif nchar != "/":
                    self.__token.append(Token('MALANGE_BRAC_OPEN', '['))
                    keyword_list: list[str] = ['script', 'for', 'while', 'if', 'switch',
                        'elif', 'else', 'case', 'default']
                else:
                    continue
                # Check for the keywords.
                keyword_found: bool = False
                for keyword in keyword_list:
                    if self.__peek(ind, keyword, file):
                        self.__token.append(Token('MALANGE_BLOCK_KEYWORD', keyword))
                        keyword_found = True
                        if keyword == "script":
                            if script_exist:
                                raise ###### ----------------------------- ##############
                            else:
                                about_to_process = "python"
                        break
                ##### -------------------------------- #####
                if not keyword_found: raise
                inside_open_mala_block = True
                open_mala_ind = ind

            # ===================== Check for ] (also contains Python processing)
            elif pchar != r"\\" and char == "]" and not inside_brac and not comment:
                record_ptext = True
                if about_to_process == "python":
                    process_arguments(self.__token,
                                      open_mala_ind, ind, 'MALANGE_BLOCK_ATTR', "script")
                else:
                    process_arguments(self.__token,
                                      open_mala_ind, ind, 'MALANGE_BLOCK_ATTR')
                self.__token.append(Token('MALANGE_BRAC_CLOSE', ']'))
                open_mala_ind = -1 ; inside_open_mala_block = False
                if about_to_process == "python": # Begin processing script blocks.
                    if script_outsourced:
                        file = access_file(script_source)
                        tokens, last_ind = pymalange_tokenize(file)
                    else:
                        # self.__process_script will return the PyTokens and the rest of the file post-script block.
                        tokens, last_ind = pymalange_tokenize(self.__file[ind+len("script"):])
                    # Then we add the tokenized Python code to a special variable.
                    self.__pytoken = tokens
                    if script_outsourced:
                        self.__lexer(file[ind:], True)
                    else:
                        # Recursive function to tokenize the rest of the code.
                        self.__lexer(file[last_ind:], True)
                    break # We break the main lexing process since the rec. lexer has done the lexing.

            # ===================== Check for ${
            elif pchar != r"\\" and char == "$" and nchar == "{" and not inside_brac and not comment:
                cleanup_ptext(self.__token)
                self.__token.append(Token('MALANGE_WRAP_OPEN', '${'))
                open_brac_ind = ind
                inside_brac = True

            # ===================== Check for }
            elif pchar != r"\\" and char == "}" and not inside_brac and not comment:
                record_ptext = True
                ref_object: str = file[open_brac_ind+1:ind]
                self.__token.append(Token('MALANGE_WRAP_EXPRE', ref_object)) # Save it.
                self.__token.append(Token('MALANGE_WRAP_CLOSE', '}'))
                inside_brac = False
                open_brac_ind = -1

            # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>> HTML TAGS

            # ===================== Check for <, </, and <!--
            elif char == "<" and not inside_open_mala_block and not inside_brac and pchar != r"\\" and not comment:
                cleanup_ptext(self.__token)
                # Check for </
                if nchar == "/":
                    self.__token.append(Token('HTML_TAG_OPEN', '</'))
                # Check for <!-- ... -->, which indicates comment.
                elif nchar == "!":
                    try: third = self.__file[ind+2]
                    except IndexError: third = None
                    try: fourth = self.__file[ind+3]
                    except IndexError: fourth = None
                    if third == "-" and forth "-":
                        comment = True
                # Check for <
                else:
                    self.__token.append(Token('HTML_TAG_OPEN', '<'))
                    inside_open_html_ele = True # So that the cursor will begin detecting = for attrs.
                # Check for the keywords.
                keyword: str = self.__trace_whitespace(ind, file)
                open_html_ind = ind + len(keyword) # Set the open_html_ind
                ##### -------------------- #####
                if keyword == "":
                    raise
                elif keyword == "script": # Begin processing script blocks.
                    about_to_process = "js"
                elif keyword == "style": # Begin processing script blocks.
                    about_to_process = "style"
                self.__token.append(Token('HTML_ELEM_KEYWORD', keyword))

            # ===================== Check for >, -->, and JS-style codes.
            elif char == ">" and not inside_open_mala_block and not inside_brac and pchar != r"\\":
                if comment:
                    try: dpchar = self.__file[ind-2]
                    except IndexError: dpchar = None
                    if char == "-" and dpchar == "-":
                        comment = False
                else:
                    record_ptext = True
                    process_arguments(self.__token, open_html_ind, ind, 'HTML_ELEM_ATTR')
                    self.__token.append(Token('HTML_TAG_CLOSE', '>'))
                    open_html_ind = -1 ; inside_open_html_ele = False
                    if about_to_process == "js":
                        if js_outsourced:
                            f = access_file(js_source)
                            self.__tokens.append('HTML_JS_SCRIPT', f) # Turned into an element.
                            self.__lexer(file[ind:])
                        else:
                            f, last_ind = process_js([ind+len("script"):])
                            self.__tokens.append('HTML_JS_SCRIPT', f)
                            self.__lexer(file[last_ind:])
                        break # After recursive lexing we terminate the main lexing process.
                    elif about_to_process == "style":
                        if style_outsourced:
                            f = access_file(style_source)
                            self.__style += f # Saved into an instance variable of the class.
                            self.__lexer(file[ind:])
                        else:
                            f, last_ind = process_style([ind+len("script"):])
                            self.__style += f
                            self.__lexer(file[last_ind:])
                        break # After recursive lexing we terminate the main lexing process.
                    else:
                        pass
            
            # ===================== Record plain text.
            else:
                if record_ptext and not comment:
                    ptext = ptext + char
                else:
                    continue
                    

    def __peek(self, ind: int, string: str, file: str) -> bool:
    '''Peek over several characters to detect multiple chars in tokenizing.'''
    length: int = len(string)
    try:
        if file[ind:ind + length] == string: return True
        else: return False
    except IndexError: return False

    def __trace_whitespace(self, ind: int, file: str) -> str:
    '''Peek over several characters until a whitespace is detected.'''
    string: str = ""
    for i in file[ind:]:
        if i.isspace():
            return string
        else:
            string = string + i
    return string # If it is empty return it.

