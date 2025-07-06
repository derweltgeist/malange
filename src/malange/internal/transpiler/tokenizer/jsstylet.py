'''

    malange.internal.transpiler.tokenizer.jsstylet

    jsstylet = JS and Style Tokenizer

    It is not exactly a tokenizer, it merely grab the text.
    That's all (except the styles).

'''

from typing import Optional, Union

def process_style(string: str) -> Union[str, int]:
    '''
    Process style script. A string of text will
    be passed to the function. The string of text must be a style-in-HTML
    text. If HTML part exists before the style part, the HTML part must be
    cleared before calling this function. Then the style will be processed
    until '</' is found, which means ending the for loop and returning the
    style text and the rest of the text seperately. Unlike JS scripts
    process_style will tokenize the styles.

    TOKENS THAT ARE DETECTED:

    CSS_SEPE_CURLL    {
    CSS_SEPE_CURLR    }
    CSS_SEPE_SCOLON   ;
    CSS_SEPE_COLON    :
    CSS_SELECT_UNI    *
    CSS_SELECT_ROOT   :root
    CSS_SELECT_MOMEN  :hover
    CSS_SELECT_PARENT &
    CSS_SELECT_CLASS  .rect, .container          Detect . durin
    CSS_SELECT_ID     #my-block, #my-div
    CSS_SELECT_TYPE   div, text, p, h1
    CSS_DATA_PROPER   background-color, color
    CSS_DATA_VALUE    yellow, black
    CSS_DATA_HEX      #00FF44
    CSS_DATA_VAR      var(...)

    parameters:
        string: str = The string of text, usually a text file string
                      passed to the function.
    returns
        1:      str = The style text.
        2:      str = The rest of the text.
    '''

    data:     str = ""
    last_ind: int = -1

    for ind, char in enumerate(string):

        try:
            nchar: Optional[str] = string[ind+1]
        except IndexError:
            nchar: Optional[str] = None

        if char == "<" and nchar == "/":
            last_ind = ind - 1
            break
        else:
            data += char

    return data, last_ind

def process_js(string: str) -> Union[str, int]:
    '''
    Process JS script into a token. A string of text will
    be passed to the function. The string of text must be a JS-in-HTML
    text. If HTML part exists before the JS part, the HTML part must be
    cleared before calling this function. Then the JS will be processed
    until '</' is found, which means ending the for loop and returning the
    JS text and the rest of the text seperately.

    parameters:
        string: str = The string of text, usually a text file string
                      passed to the function.
    returns:
        1:      str = The JS text.
        2:      int = The last index.
    '''

    data:     str = ""
    last_ind: int = -1

    for ind, char in enumerate(string):

        try:
            nchar: Optional[str] = string[ind+1]
        except IndexError:
            nchar: Optional[str] = None

        if char == "<" and nchar == "/":
            last_ind = ind - 1
            break
        else:
            data += char

    return data, last_ind
