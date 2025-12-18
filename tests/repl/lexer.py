token = []

from typing import Optional

class Token:
    '''For Malange tokens.'''
    def __init__(self, token: str = "",
                 value: str = "", ind: int = 0) -> None:
        self.token: Optional[str] = token
        self.value: Optional[str] = value
        self.ind:   Optional[int] = ind
    def __call__(self) -> str:
        if self.value is not None:
            refresh = self.value.replace('\n', r'\n')
        else:
            print("Error when refreshing...")
            exit(1)
        return f"{self.token} [{self.ind}] : '{refresh}'"


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

def process_html_tag(file: str, sind: int):
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
    js:           bool = False
     
    # Main loop.
    while ind < len(file):
         # nchar = Next character, pchar = Previous character,
         # char = Current character, nnchar = Double next char
         char = file[ind]
         print(f"[HTML] Now scanning character '{char}' of primary index [{sind+ind+1}] and secondary index [{ind}]")
         try:
             nchar: str = file[ind+1]
         except IndexError:
             nchar: str = ""
 
         # 1-- Check for whether the opening bracket is part of a start tag (<) or end tag (</)
         if ind == 0: # On index 0m the character is either / (closing tag) or non-/ (opening tag)
            if char == "/":
                # This means a HTML closing tag.
                token.append(Token('HTML_TAG_MID', '</', sind+ind))
                end = True # Enable the close variable to True.
                # Skip to the next char for keyword record (next block)
                ind += 1
                continue # Skip to the next char (the keyword).
            else:
                token.append(Token('HTML_TAG_OPEN', '<', sind+ind))

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
                    print(
                        f"[HTML] Error in primary index [{sind+keyword_ind}]: When processing keyword the keyword is empty.")
                    exit(1)
                if keyword.strip() == "script":
                    js = True
                token.append(Token('HTML_ELEMENT_KEYWORD', keyword, sind+keyword_ind))
                attr_ind = ind + 1
            elif char in ("=", '"', "'", "<", "`", "\\"): # A keyword that contains these chars is not accepted.
                print(
                f"[HTML] Error in primary index [{sind+ind-1}]: when processing keyword the forbidden character '{char}' is detected.")
                exit(1)
            else:
                keyword += char # Anything other than that just add to the keyword.

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
                    token.append(Token('HTML_ELEMENT_ATTR', attr, sind+attr_ind))
                token.append(Token('HTML_TAG_CLOSE', '>', sind+ind))
                break # Exit the loop.
            elif char == '/' and nchar == '>' and not attr_str_on:
                ind += 2
                if attr != "":
                    token.append(Token('HTML_ELEMENT_ATTR', attr, sind+attr_ind))
                token.append(Token('HTML_TAG_SELFCLOSE', '/>', sind+ind-1))
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
         elif check_attr and end:
            if char == '/' and nchar == '>':
                token.append(Token('HTML_TAG_SELFCLOSE', '/>', sind+ind+1))
                ind += 2
                break
            elif char == '>':
                token.append(Token('HTML_TAG_CLOSE', '>', sind+ind+1))
                ind += 1
                break
            elif char.isspace():
                ind += 1
                continue
            else:
                print(f"[HTML] Error in primary index [{sind+ind}]: An attribute can't exist in an end tag.")
                exit(1)
         ind += 1
    return sind+ind, js

def process_malange_tag(file: str, sind: int) -> tuple[int, bool]:
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
            file:                      str    = The file string text.
            start_ind:                 int    = The index of the '/', NOT '['
        returns:
            1:                         int    = The last primary index of /]
        errors:
            syntax.malange.invalidopentag     = Invalid open tag, eg ' ..' or a HTML tag containing quotes, `, <, =
            syntax.malange.attronclosing      = Usage of attributes on a closing tag.
            syntax.malange.invalidcharkeyword = HTML tag containing quotes, `, <, =.
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
    component:     bool = False
    
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
                token.append(Token('MALANGE_TAG_OPENSLASH', '[/', sind+ind-1))
                close = True # Enable the close variable to True.
                # Skip to the next char for keyword record (next block)
                ind += 1
                continue # Skip to the next char (the keyword).
            else:
                token.append(Token('MALANGE_TAG_OPEN', '[', sind+ind-1))

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
                    print(
                        f"[MALANGE] Error in primary index [{sind+keyword_ind}]: When processing keyword the keyword is empty.")
                    exit(1)
                if keyword in ("elif", "else", "case") and close: # [elif/], [else/], and [case/]
                    print(f"[MALANGE] Error in primary index [{sind+keyword_ind}]: elif, else, and case can only be used with begin tag")
                    exit(1)
                # We check if the keyword is a keyword or a component injection.
                if keyword in ("script", "for", "while", "if", "elif", "else", "switch", "case"):
                    if keyword == "script": # After [script/] The next code is Python.
                        python = True
                        token.append(Token('MALANGE_ELEMENT_KEYWORD', keyword, sind+keyword_ind))
                else:
                    # If it is not a keyword, it must be a component injection. Which must follow this: [/x/]
                    if close: # Thus close must be True
                        component = True # When checking for closing bracket, we must ensure the closing is /] and not ]
                        token.append(Token('MALANGE_ELEMENT_COMPONENT', keyword, sind+keyword_ind))
                    else:
                        print(f"[MALANGE] Error in primary index [{sind+keyword_ind}]: A component injection must follow [/.../]")
                        exit(1)
            # Again such special characters are forbidden.
            elif char in ("=", '"', "'", "[", "`", "\\", "$", "%", "@", "#", "!", "%", "^", "&",
                          "*", "(", ")", "-", "+", ":", ";", "{", "}", "|", "<", ">", "?", "`"):
                print(
                f"[MALANGE] Error in primary index [{sind+ind-1}]: when processing keyword the forbidden character '{char}' is detected.")
                exit(1)
            else:
                keyword += char # Anything other than that just add to the keyword.

        # 3-- If keyword checking is disabled via check_args == True, add the char to the arguments.
        # --- If ] or /] is dicovered, exit Malange tag scanning.
        # --- It will parse string/number/injection of a Malange argument.
        # --- This will immediately run after keyword scanning is disabled.
        if check_args and not close:
            # If ] is discovered and is not currently recording a string.
            if char == ']' and pchar != "/" and not args_str_on:
                print(f"[MALANGE] Error in the primary index {sind+ind}: Invalid begin tag, it should be [../].")
                exit(1)
            elif char == '/' and nchar == ']' and not args_str_on:

                ind += 2
                token.append(Token('MALANGE_ELEMENT_ATTR', args, sind+args_ind))
                token.append(Token('MALANGE_TAG_CLOSESLASH', '/]', sind+ind))
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
                token.append(Token('MALANGE_TAG_CLOSE', ']', sind+ind))
                break
            elif char == "/" and nchar == "]":
                if component:
                    ind += 2
                    token.append(Token('MALANGE_TAG_CLOSESLASH', '/]', sind+ind))
                else:
                    print(f"[MALANGE] Error in primary index {sind+ind+1}: Invalid component tag. Make sure you do not use keywords.")
                    exit(1)
            elif char.isspace():
                ind += 1
                continue
            else:
                print(f"[MALANGE] Error in primary index {sind+ind+1}: Attributes can not be put inside an end Malange tag.")
                exit(1)
        ind += 1
    return sind+ind, python

# JS state variables.
mode:           str  = "normal"
js_text:        str  = ""       # js string.
js_comment:     str  = ""       # whether js scanning is entering commenting mode.
js_string:      str  = ""       # js string type (single quote or double quote or empty aka none)
js_cont_str:    bool = False    # this variable is for line continuation of single-line strings
js_ind:         int  = 0        # first index of js.


def process_js_text(char: str, pchar: str, nchar: str, ind: int) -> None:
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
    '''

    global js_text, js_comment, js_string, js_cont_str, js_ind

    # 1-- Comment detection.
    # If / is detected (and ensuring commenting and string is disabled)...
    if char == "/" and js_comment == "" and js_string == "":
        if nchar == "/": # If //, this means single line commenting is on
            js_comment = "sl"
        elif nchar == "*": # If /*, this means multi line commenting is on
            js_comment = "ml"
        else: # If it is just /, treat it usual
            if pchar == "/":
                pass
            else:
                js_string += char

    # 2-- If \ is detected, since this is a way you perform multiline strings for ' and "
    # e.g. like this:
    #   x = "abc \
    #   xyz"
    # this has to be taken into account. Thus js_const_str will be enabled
    # That variable if set to True means line continuation of single-line strings is True.
    elif char == "\\" and js_comment == "" and js_string in ("'", '"'):
        js_cont_str = True
        js_text += char

    # 3-- Newline is detected, which means...
    elif char == "\n":
        # For single line string, this means termination of string mode.
        # But if js_const_str is enabled, string mode will continue.
        if js_string in ('"', "'"):
            if js_cont_str:
                js_cont_str = False
                js_text += char
            else:
                print(f"[JS] Error in primary index {ind}: Invalid string termination, no backslash is present too.")
                exit(1)
        # If the comment is single line, disable the commenting mode.
        if js_comment == "sl":
            js_comment = ""

    # 4-- This means termination for multiline comment, only if string mode is off
    elif char == "*" and nchar == "/" and js_comment == "ml" and js_string == "":
        js_comment = ""

    # 5-- String detection, only if commenting is disabled.
    elif char in ('"', "'", '`') and pchar != "\\" and js_comment == "":
        if js_string == "":
            js_string = char # Save the type of string initializer.
        else:
            if js_string == char:
                js_string = ""
        js_text += char

    # 6-- For normal JS char, just record it normally.
    else:
        if js_comment == "":
            js_text += char

py_exist:       bool = False    # Whether a [script/] tag has existed or not.
py_text:        str  = ""       # Py string.
py_comment:     bool = False    # whether js scanning is entering commenting mode.
py_ind:         int  = 0        # first index of Python index.
py_cont_str:    bool = False

py_string:      bool = False
py_string_f:    bool = False
py_string_r:    bool = False
py_string_dq:   bool = False
py_string_tr:   bool = False


def process_py_text(char: str, pchar: str, ppchar: str, nchar: str, nnchar: str, ind: int) -> int:
    '''
        Process Python text. The way it works is like this:
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
    global py_exist, py_string, py_ind, py_string_dq, py_cont_str
    global py_comment, py_string_f, py_string_r, py_string_tr, py_text

    # 1-- Comment detection.
    # If / is detected (and ensuring commenting and string is disabled)...
    if char == "#" and not py_comment and not py_string:
        py_comment = True

    # 2-- If \ is detected, since this is a way you perform multiline strings for ' and "
    # e.g. like this:
    #   x = "abc \
    #   xyz"
    # this has to be taken into account. Thus js_const_str will be enabled
    # That variable if set to True means line continuation of single-line strings is True.
    elif (char == "\\" and not py_comment and py_string
          and not py_string_tr and not py_string_f):
        py_cont_str = True
        py_text += char

    # 3-- Newline is detected, which means...
    elif char == "\n":
        # For single line string, this means termination of string mode.
        # But if py_const_str is enabled, string mode will continue.
        if py_string and not py_string_tr:
            if py_cont_str:
                py_cont_str = False
                py_text += char
            else:
                print(f"[PYTHON] Error at primary index [{ind}]: Invalid string termination")
                exit(1)
        # If the comment is single line, disable the commenting mode.
        elif py_comment:
            py_comment = False
        else:
            py_text += char

    # 4-- String detection, only if commenting is disabled.
    elif char in ('"', "'") and not py_comment:
        if pchar == "\\": # Check the escape
            if py_string_r: # if it is a raw string ignore the escape
                pass
            else:
                py_text += char # The escape has been recorded the prev. loop
                return 0
        # First we will detect whether it is closing or opening
        if py_string: # Which means the closing of the string.
            # Check if the scanned char is a triple quote or not.
            if nchar == char and nnchar == char:
                if char == '"': # We will check whether the type is the same.
                    dq = True
                else:
                    dq = False
                if py_string_tr: # If yes, this means the closing and opening are triple
                    if dq == py_string_dq: # Yes? Close.
                        py_string    = False # To ensure full reset.
                        py_string_dq = False
                        py_string_f  = False
                        py_string_r  = False
                        py_string_tr = False
                    # If it does not close, no reset and continue.
                    else:
                        pass
                else: # Indicating that the opening string is not triple.
                    if dq == py_string_dq: # Aka " .... """ which is not valid
                        print(f"[PYTHON] Error at primary index [{ind}]: Invalid string termination")
                        exit(1)
                    else:
                        pass
                py_text += f"{char}{nchar}{nnchar}" # Add the chars and jump by 2.
                jump = 2
            else: # If the char is not a triple quote...
                if char == '"': # Check the type. 
                    dq = True
                else:
                    dq = False
                if dq == py_string_dq: # If it is the same type:
                    if py_string_tr: # Basically e.g. " ... """ .., it is invalid
                        print(f"[PYTHON] Error at primary index [{ind}]: Invalid string termination")
                        exit(1)
                    else: # Basically e.g. " ... " ..., which is valid
                        py_string    = False # To ensure full reset.
                        py_string_dq = False
                        py_string_f  = False
                        py_string_r  = False
                        py_string_tr = False # If it does not close, it won't close.   
                        py_text += f"{char}"
                else: # If it not the same type, just add it like normal eg """ ... ' or " ... '
                    py_text += f"{char}"
        else: # Which means the opening of the string.
        # Enable self.__py_string first
            py_string = True
            # Check if it is single quote or not.
            if char == '"':
                py_string_dq = True
                py_text += '"'
            elif char == "'":
                py_string_dq = False
                py_text += "'"
            # First analyze the f and r prefix.
            if pchar in ("F", "f"):
                py_string_f = True
                if ppchar in ("R", "r"):
                    py_string_r = True
            elif pchar in ("R", "r"):
                py_string_r = True
                if ppchar in ("F", "f"):
                    py_string_f = True
            # Second we will analyze whether it is a triple quote or not.
            if nchar == char and nnchar == char:
                py_string_tr = True
                py_text += f"{nchar}{nnchar}" # The f/F and r/R has been recorded in the previous loop.
                jump = 2 # We want to skip the nchar and nnchar.
    # 6-- For normal PY char, just record it normally.
    else:
        if not py_comment:
            py_text += char
    return jump

def main(file):


    global js_text, js_comment, js_string, js_cont_str, js_ind, mode, py_exist, py_text
    global py_string_dq, py_string_f, py_string_r, py_string_tr, py_string, py_ind

    ind: int = 0     # Primary index.

    print(f"Scan text: '{file}'")
    print("-------------")


    # Begin looping over file char by char. We use WHILE to allow us to jump iterations,
    # thus making tokenizing significantly easier.
    while ind < len(file):

        # nchar = Next character, pchar = Previous character, char = Current character
        char = file[ind]
        try:
            nchar: str = file[ind+1]
        except IndexError:
            nchar: str = ""
        if ind - 1 < 0:
            pchar: str = ""
        else:
            pchar: str = file[ind-1]
        if ind - 2 < 0:
            ppchar: str  = ""
        else:
            ppchar: str  = file[ind-2]
        try:
            nnchar: str = file[ind+2]
        except IndexError:
            nnchar: str = ""

        if char != '\n':
            refreshed_char = char
        else:
            refreshed_char = r'\n'
        print(f"[MAIN] Now scanning char '{refreshed_char}' of primary index '{ind}', mode is [{mode}].")
        
        # === A: Normal mode.
        if mode == "normal":
            # Check for Malange tags.
            if pchar != "\\" and char == "[":
                new_ind, python = process_malange_tag(file[ind+1:], ind+1)
                ind = new_ind
                if python:
                    if not py_exist:
                        py_exist = True
                        mode = "python"
                        py_ind = ind+1
                    else:
                        print(f"[MAIN] Error at primary index [{ind}]: You can not have multiple Malange script.")
                        exit(1)
            # Check for HTML tags.
            elif pchar != "\\" and char == "<":
                new_ind, js = process_html_tag(file[ind+1:], ind)
                if js:
                    mode = "js"
                    js_ind = new_ind + 1
                    js = False
                ind = new_ind
       # === B: Check for Python.
        elif mode == "python":
            if char == "[" and nchar == "/" and not py_comment and not py_string:
                if not py_text.isspace():
                    token.append(Token('MALANGE_ELEMENT_PY',  py_text, py_ind))
                py_text        = ""
                py_ind         = 0
                mode           = "normal"
                py_string      = False
                py_string_dq   = False
                py_string_f    = False
                py_string_r    = False
                py_string_tr   = False
                new_ind, py    = process_malange_tag(file[ind+1:], ind)
                if not py:
                    print("[MALANAGE] Error at primary index [{ind}]: [script/] is unterminated") 
                else:
                    ind = new_ind
            else:
                jump = process_py_text(char, pchar, ppchar, nchar, nnchar, ind)
                ind += jump

        # === C: Check for JS.
        elif mode == "js":      
            if char == "<" and nchar == "/" and js_comment == "" and js_string == "":
                js_comment = ""
                if js_text.isspace():
                    js_text = ""
                else:
                    token.append(Token('HTML_ELEMENT_JS', js_text, js_ind))
                    js_text = ""
                js_ind = 0
                mode = "normal"
                new_ind, js = process_html_tag(file[ind+1:], ind)
                if not js:
                    print(f"[JS] Error in primary index [{ind}]: <script> is not closed.")
                    exit(1)
                else:
                    ind = new_ind
            # 7-- For normal JS char, just record it normally.
            else:
                process_js_text(char, pchar, nchar, ind)
        ind += 1
    if mode == "js":
        print("[JS] Error at the end of file: <script> is not closed.")
        exit(1)
    elif mode == "python":
        print("[PYTHON] Error at the end of file: [script/] is not closed.")
        exit(1)
    print("-------------")
    print("TOKEN RESULT:")
    for i, t in enumerate(token):
        print(f"{i} > {t()}")

file = r'''
[script/]
R" sdsds \
dsds"
'''
#        012345678911111111112222222222333    primary
#                  01234567890123456789012
#          012456                  secondary (for opening)
#                        0123456         secondary (for closing)

main(file)
