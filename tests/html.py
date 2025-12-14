def __process_html_tag(file: str, sind: int):
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
    print(f"[SECOND] SIND IS {sind}")
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
                print("[SECOND/BEGIN/CLOSE] IT IS CLOSE")
                close = True
                if nchar.isspace():
                    print("ERROR < IS FOLLOWED BY SPACE")
            else:
                print("[SECOND/BEGIN/OPEN] IT IS OPEN")
                if char.isspace():
                    print("ERROR < 59 IS FOLLOWED BY SPACE")
        if not check_args:
            if not keyword_begin: # Again apply the same technique from Malange block args tokenization.
                keyword_ind = ind
                keyword_begin = True
            if ind == 0 and char == "/":
                ind += 1
                continue
            if char.isspace() or char == ">" or (char == "/" and nchar == ">"):
                print(f"KEYWORD ENDS WITH ({keyword}), char ({char}), nchar ({nchar}), pchar ({pchar}), nnchar ({nnchar})")
                check_args = True # Begin checking for arguments at the next char, no more keyword scans.
                if keyword.isspace() or keyword == "":
                    print("ERROR INVALID KEYWORD")
            elif char in ("=", '"', "'", "`", "\\", "<"):
                print("ERROR INVALID KEYWORD NO SPECIAL CHAR")
            else:
                keyword += char

        # --- If keyword checking is disabled via check_args == True, add the char to the arguments.
        #     If unescaped ] is dicovered, exit tag processing.
        #     If escaped ] is discovered, add only the ] to the arguments.
        if check_args and not close:
            print(f"[SECOND/ARGS/OPEN] KEYWORD IS {keyword}")
            if pchar not in ('/', '\\') and char == '>': # If this char is discovered, end the recording of the HTML tag.
                # You can't insert attributes into a closing tag, so no.
                ind += 1
                print(f"[SECOND/END/OPEN] END WITH >, current char is {char}, index is {sind+ind}")
                
                print(f"[SECOND/END/OPEN] ARGS ARE ({args})")

                break # Exit the loop.
            elif pchar != '\\' and char == '/' and nchar == '>': # This indicates /> ending.
                ind += 2
                print(f"[SECOND/END/OPEN] END WITH />, current char is {char}, index is {sind+ind}")
                
                print(f"[SECOND/END/OPEN] ARGS ARE ({args})")
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
            print(f"[SECOND/ARGS/CLOSE] KEYWORD IS {keyword}")
            if pchar != '\\' and char == '>':
                ind += 1
                print(f"[SECOND/END/CLOSE] CLOSE END WITH >, current char is {char}, index is {sind+ind}")            
                break
            elif char.isspace():
                ind += 1
                continue
            else:
                if char == '\\' and nchar == '>':
                    args += '>'
                    ind += 1
                print(char)
                print("INVALID CLOSING TAG")

        print(f"[SECOND] Secondary Index is {ind}")
        ind += 1
    return sind+ind

def main():
    file = r"a<habcwelcome</habc/>abc"
#           012345678911111111112222222222333    primary
#                     01234567890123456789012
#             012456                  secondary (for opening)
#                                0123456         secondary (for closing)
    i = 0
    while i < len(file):
        char = file[i]
        if i-1 >= 0:
            pchar = file[i-1]
        else:
            pchar = ""
        try:
            nchar = file[i+1]
        except IndexError:
            nchar = ""
        print(f"[PRIMARY] CURRENTLY SCANNING: ({char})")
        if char == "<" and pchar != "\\":
            print(f"[PRIMARY] starting index of < is: {i}")

            final_ind = __process_html_tag(file[i+1:], i)
            i = final_ind
            print(f"[PRIMARY] ending index of > is: {final_ind}")
        elif char == "\\" and nchar == "<":
            print("[PRIMARY] SKIPPING ESCAPE CHAR")
        else:
            print(f"[PRIMARY] NON-SECONDARY CHAR: ({char})")
        i += 1

main()
