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
        self.__script:  bool        = False
        # self.__plain:   bool        = False
        # self.__python:  bool        = False
        # self.__comment: bool        = False
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
                and type_mala_tag. type_html_tag can be "open" (< .. <) or "close" (</ ...).
            -   Same with type_mala_tag. If an injection expression eg ${ ... } is encountered it will also
                set inside_brac to True. The start_brac_ind is the index for ${ for grabbing expressions
                from inside ${ ... } through slicing file.
            -   Same for start_mala_ind for Malange blocks and start_html_ind for HTML elements for grabbing arguments.
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

            # ===================== Check for Malange Tags
            if pchar != "\\" and char == "[" and self.__mode == "normal":
                new_ind = self.__process_mala_tag(file[ind:], ind+1)
                ind = new_ind

            ind += 1
    
    def __process_mala_tag(self, file: str, sind: int) -> int:
        '''
            Created to process malange tag tokens. The mechanism is like this:
            - First it will begin by scanning whether the tag is closed or not.
            - Second it will begin by scanning the keyword.
            - Third it will scan arguments (only scanned if the tag is not closing tag)
            - Fourth it will finish when ']' is discovered.
            The process of finishing is like this:
            - Begin by compiling the arguments into a dictionary.
            - Then append the argument tokens (the final form)
            - Then append the closing tag.
            - Exit function.

            parameters:
                file: The file string text.
                start_ind: The index of the '/', NOT '['
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

        def process_arguments(arguments: str, args_ind: int) -> dict[str, str]:
            '''
            Process the arguments.
            parameters:
                arguments:    str  = The raw string arguments.
            returns:
                1:            bool = The processed dict.
            '''
            nonlocal sind
            # First, break apart the arguments by using comma as a seperator.
            split_args: list[str] = arguments.split(',')
            # Analyze each split args.
            for arg in split_args:
                try:
                    arg_name, arg_content = arg.split('=')
                else IndexError:
                    error({
                        'component' : 'syntax.malange.invalidargs',
                        'message'   : f'An argument is found invalid.',
                        'index'     : sind+args_ind
                    })
                split_args[arg_name] = arg_content.strip()

        ind:        int = 0       # Current index.
        check_args: bool = False  # Whether the argument recording is enabled or not.
        args:       str  = ""     # String variable for arguments.
        args_begin: bool = False  # Whether argument recording has begun or not.
        args_ind:   int  = 0      # The index of the first char of the arguments.
        close:      bool = False  # Whether the tag is closed or not.
        
        processed_args: dict[str, str] = {} # Processed non-raw args.

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

            # --- Check for [/
            if char == "/":
                self.__token.append(Token('MALANGE_BRAC_MID', '[/', sind+ind))
                # Several keywords don't have a closing counterpart.
                keyword_list: list[str] = ['script', 'for', 'while', 'if', 'match']
                close = True
            elif char != "/":
                self.__token.append(Token('MALANGE_BRAC_OPEN', '[', sind+ind))
                keyword_list: list[str] = ['script', 'for', 'while', 'if', 'match',
                    'elif', 'else', 'case', 'default']
            else: pass

            # --- Check for the keywords.
            if check_args == False:
                keyword_found: bool = False
                valid_keyword: str  = ""
                for keyword in keyword_list:
                    if peek(ind, keyword, file):
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
                if not keyword_found:
                    error({
                        'component' : 'syntax.malange.invalidkeyword',
                        'message'   : f'Source "{script_source}" is not found or is invalid.',
                        'index'     : sind+ind
                    })
                # Set check args as true.
                if not close:
                    check_args = True

            # --- If keyword checking is disabled via check_args == True, add the char to the arguments.
            #     If ] is dicovered, exit tag processing.
            elif check_args == True:
                if char == ']': # If this char is discovered, end the recording of the Malange tag.
                    # You can't insert attributes into a closing tag, so no.
                    if close and check_args == True:
                        error({
                        'component' : 'syntax.malange.attronclosing',
                        'message'   : f'Attribute is on a closing tag, which is invalid.',
                        'index'     : sind+ind
                        })
                    # If no error, continue.
                    process_arguments(args) # Process the arguments from a str into a dict.
                    # Append the tokens.
                    self.__token.append(Token('MALANGE_BLOCK_ATTR', args, sind+args_ind)
                    self.__token.append(Token('MALANGE_BRAC_CLOSE', ']', sind+ind)
                    break # Exit the loop.
                else: # Continue recording the arguments like normal.
                    # If this is the first time, args_begin will be disabled.
                    # Thus it will be enabled, then the args_ind will be recorded
                    # only once. After that the args_ind won't be touched again.
                    if not args_begin:
                        args_ind = ind
                        args_begin = True
                    args += char

            ind += 1
        return start_ind+ind
