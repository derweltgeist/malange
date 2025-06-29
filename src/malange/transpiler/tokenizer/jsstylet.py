'''

    malange.transpiler.tokenizer.jsstylet

    jsstylet = JS and Style Tokenizer

    It is not exactly a tokenizer, it merely grab the text.
    That's all.

'''

from typing import Optional, Union

def process_js(string: str) -> Union[str, str]:

    data:     str = ""
    last_ind: int = -1

    for ind, char in enumerate(string):

        try:
            nchar: Optional[str] = string[ind+1]
        except IndexError:
            nchar: Optional[str] = None

        if char == "<" and nchar == "/":
            last_ind = ind
            break
        else:
            data += char

    if last_ind == -1:
        return data, ""
    else:
        return data, string[last_ind-1:]


def process_style(string: str) -> Union[str, str]:

    data:     str = ""
    last_ind: int = -1

    for ind, char in enumerate(string):

        try:
            nchar: Optional[str] = string[ind+1]
        except IndexError:
            nchar: Optional[str] = None

        if char == "<" and nchar == "/":
            last_ind = ind
            break
        else:
            data += char

    if last_ind == -1:
        return data, ""
    else:
        return data, string[last_ind-1:]
