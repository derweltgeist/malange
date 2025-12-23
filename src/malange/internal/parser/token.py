'''

    malange.internal.transpiler.tokenizer.token

    Manages the tokenization of Malange blocks and HTML elements.

'''

from typing import Optional

class MalangeToken:
    '''For Malange tokens.'''
    def __init__(self, token: str = "",
                 value: str = "", ind: int = 0) -> None:
        self.token: Optional[str] = token
        self.value: Optional[str] = value
        self.ind:   Optional[int] = ind
    def __call__(self) -> str:
        return f"> {self.token}({self.ind}) : '{self.value}'"

