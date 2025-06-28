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

'''

from typing import Optional

from .token import Token
from .malapyt import process_script
from .malajst import process_js, process_style

class MalangeTokenizer:
    '''Tokenizer class for each Malange file.'''
    def __init__(self, file: str):
        self.__token: list[Token] = []
        self.__token: list[Token] = []
        self.__lexer(file)
    def __lexer(self, file: str):
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
        open_brac_ind: int  = -1
        # Same idea for processing arguments. Instead of 'type' '=' 'text/javascript'
        # my idea is just to carry the entirety eg 'type=text/javascript' and process it
        # later in the parser. And yes -1 = No index.
        open_html_ind: int = -1
        # Same idea for Malange arguments.
        open_mala_ind: int = -1

        # Recording plain text.
        record_ptext: bool = True
        ptext:        str  = ""

        def cleanup_ptext():
            '''Clean up plain text.'''
            self.__token.append('HTML_PLAIN_TEXT', ptext)
            record_ptext = False
            ptext = ""

        def process_arguments(start_ind: int, end_ind: int, attr_name: str):
            '''Process args of both Malange blocks and HTML elements'''
                # Process the arguments first.
                arguments = file[star_ind+1:end_ind]
                # The validity of the arguments will be processed later in the parser.
                self.__token.append(Token(attr_name, arguments))

        for ind, char in enumerate(file):
            try:
                nchar: Optional[int] = file[ind+1]
            except IndexError: nind:
                Optional[None] = None
            if ind - 1 < 0:
                pchar: Optional[int] = None
            else:
                pchar: Optional[int] = file[ind-1]

            # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>> MALANGE BLOCKS

            # ===================== Check for [ and [/
            if pchar != r"\\" and char == "[" and not inside_brac:
                cleanup_ptext()
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
                            about_to_process = "python"
                        break
                ##### -------------------------------- #####
                if not keyword_found: raise
                inside_open_mala_block = True
                open_mala_ind = ind

            # ===================== Check for ] (also contains Python processing)
            elif pchar != r"\\" and char == "]" and not inside_brac:
                record_ptext = True
                process_arguments(open_mala_ind, ind, 'MALANGE_BLOCK_ATTR')
                self.__token.append(Token('MALANGE_BRAC_END', ']'))
                open_mala_ind = -1 ; inside_open_mala_block = False
                if about_to_process == "python": # Begin processing script blocks.
                    # self.__process_script will return the PyTokens and the rest of the file post-script block.
                    tokens, last_ind = process_script(self.__file[ind+len("script")+1:])
                    # Then we add the tokenized Python code to a special variable.
                    self.__pytoken = tokens
                    # Recursive function to tokenize the rest of the code.
                    self.__lexer(file[last_ind:])
                    break # We break the main lexing process since the rec. lexer has done the lexing.

            # ===================== Check for ${
            elif pchar != r"\\" and char == "$" and nchar == "{" and not inside_brac:
                cleanup_ptext()
                self.__token.append(Token('MALANGE_WRAP_OPEN', '${'))
                open_brac_ind = ind
                inside_brac = True
            # ===================== Check for }
            elif pchar != r"\\" and char == "}" and not inside_brac:
                record_ptext = True
                ref_object: str = file[open_brac_ind+1:ind]
                self.__token.append(Token('MALANGE_WRAP_EXPRE', ref_object)) # Save it.
                self.__token.append(Token('MALANGE_WRAP_CLOSE', '}'))
                inside_brac = False
                open_brac_ind = -1

            # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>> HTML TAGS

            # ===================== Check for < and </
            elif char == "<" and not inside_open_mala_block and not inside_brac and pchar != r"\\":
                cleanup_ptext()
                # Check for </
                if nchar == "/":
                    self.__token.append(Token('HTML_TAG_OPEN', '</'))
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

            # ===================== Check for > and JS-style codes.
            elif char == ">" and not inside_open_mala_block and not inside_brac and pchar != r"\\":
                record_ptext = True
                process_arguments(open_html_ind, ind, 'HTML_ELEM_ATTR')
                self.__token.append(Token('HTML_TAG_CLOSE', '>'))
                open_html_ind = -1 ; inside_open_html_ele = False
                if about_to_process == "js":
                    # First the open JS token.
                    self.__token.append(Token('HTML_JS_OPEN', None))
                    # Then we begin processing.
                    tokens, last_ind = process_js(
                        self.__file[ind+len("script")+1:])
                    # Then we add the tokenized JS code.
                    self.__token = self.__token + tokens
                    # Then we end it with the closing JS token.
                    self.__token.append(Token('HTML_JS_CLOSE'. None))
                    # Recursive function to tokenize the rest of the code.
                    self.__lexer(file[last_ind:])
                    break # After recursive lexing we terminate the main lexing process.
                elif about_to_process == "style":
                    # First the open CSS token.
                    self.__token.append(Token('HTML_STYLE_OPEN', None))
                    # Then we begin processing.
                    tokens, last_ind = process_style(
                        self.__file[ind+len("script")+1:])
                    # Then we add the tokenized CSS code.
                    self.__token = self.__token + tokens
                    # Then we end it with the closing CSS token.
                    self.__token.append(Token('HTML_STYLE_CLOSE', None))
                    # Recursive function to tokenize the rest of the code.
                    self.__lexer(file[last_ind:])
                    break # After recursive lexing we terminate the main lexing process.
            
            # ===================== Record plain text.
            else:
                if record_ptext:
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
        '''Peek over several characters until a whitespace is detected.''''
        string: str = ""
        for i in file[ind:]:
            if i.isspace():
                return string
            else:
                string = string + i
        return spring # If it is empty return it.

