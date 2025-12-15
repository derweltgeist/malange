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
        return f"{self.token} [{self.ind}] : '{self.value}'"

def __process_html_tag(file: str, sind: int):
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
    
    # Main loop.
    while ind < len(file):
        # nchar = Next character, pchar = Previous character,
        # char = Current character, nnchar = Double next char
        char = file[ind]
        print(f"[SECONDARY] Now scanning character '{char}' of primary index [{sind+ind+1}] and secondary index [{ind}]")
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
                        f"[SECONDARY] Error in primary index [{sind+keyword_ind}]: When processing keyword the keyword is empty.")
                    exit(1)
                token.append(Token('HTML_ELEMENT_KEYWORD', keyword, sind+keyword_ind))
                attr_ind = ind + 1
            elif char in ("=", '"', "'", "<", "`", "\\"): # A keyword that contains these chars is not accepted.
                print(
                f"[SECONDARY] Error in primary index [{sind+ind-1}]: when processing keyword the forbidden character '{char}' is detected.")
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
                print(f"[SECONDARY] Error in primary index [{sind+ind}]: An attribute can't exist in an end tag.")
                exit(1)
        ind += 1
    return sind+ind

def main():
    file = r'a<abc> abcdefg </habc>abc'
#            012345678911111111112222222222333    primary
#                      01234567890123456789012
#             012456                  secondary (for opening)
#                              0123456         secondary (for closing)
    i = 0
    print(f"Scan text: '{file}'")
    print("-------------")
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
        print(f"[PRIMARY] Now scanning character '{char}' of index [{i}]")
        if char == "<" and pchar != "\\":
            print(f"[PRIMARY] Entering secondary, starting index of < is: [{i}]")

            final_ind = __process_html_tag(file[i+1:], i)
            i = final_ind
            print(f"[PRIMARY] Exiting secondary, ending index of > is: [{final_ind}]")
        elif char == "\\" and nchar == "<":
            print("[PRIMARY] Skipping escape character.")
        else:
            print(f"[PRIMARY] Character is pure primary.")
        i += 1
    print("-------------")
    print("TOKEN RESULT:")
    for i, t in enumerate(token):
        print(f"{i} > {t()}")

main()
