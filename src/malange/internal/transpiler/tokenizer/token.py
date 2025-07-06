'''

    malange.internal.transpiler.tokenizer.token

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

    - MALANGE_BRAC_MID      [/ # Required to detect the ending script tag.

    - PYTHON_WS_GEN         Generic whitespace: space and tab.
    - PYTHON_WS_NL          cr ln ln cr # Any kind of new line.

    - PYTHON_MARK_CURVL     (    PYTHON_MARK_CURVR     )    
    - PYTHON_MARK_SQURL     [    PYTHON_MARK_SQURR     ]
    - PYTHON_MARK_CURLL     {    PYTHON_MARK_CURLR     }
    - PYTHON_MARK_DOT       .    PYTHON_MARK_COMMA     ,
    - PYTHON_MARK_COLON     :    PYTHON_MARK_SCOLON    ;
    - PYTHON_MARK_DCOLON    ::

    - PYTHON_OP_PLUS        +    PYTHON_OP_MINUS       -
    - PYTHON_OP_STAR        *    PYTHON_OP_SLASH       /
    - PYTHON_OP_DTAR        **   PYTHON_OP_DSLASH      //
    - PYTHON_OP_TILDE       ~    PYTHON_OP_CARET       ^
    - PYTHON_OP_AMPSAND     &    PYTHON_OP_GRAVE       `
    - PYTHON_OP_SLEFT       <<   PYTHON_OP_SRIGHT      >>
    - PYTHON_OP_PERCENT     %
       
    - PYTHON_AS_PLUS        +=   PYTHON_AS_MINUS       -=
    - PYTHON_AS_STAR        *=   PYTHON_AS_SLASH       /=
    - PYTHON_AS_DTAR        **=  PYTHON_AS_DSLASH      //=
    - PYTHON_AS_TILDE       ~=   PYTHON_AS_CARET       ^=
    - PYTHON_AS_AMPSAND     &=   PYTHON_AS_GRAVE       `=
    - PYTHON_AS_SLEFT       <<=  PYTHON_AS_SRIGHT      >>=
    - PYTHON_AS_DEFINE      =    PYTHON_AS_PERCENT     %=

    - PYTHON_CP_EQUAL       ==   PYTHON_CP_NOEQUAL     !=
    - PYTHON_CP_LESSEQ      <=   PYTHON_CP_MOREEQ      >=
    - PYTHON_CP_LESS        <    PYTHON_CP_MORE        >

    - PYTHON_SPEC_QUOT      " '
    - PYTHON_SPEC_DOCSTR    """, etc
    - PYTHON_SPEC_CONT      /
    
    - PYTHON_GEN_LITERAL    2323, DFDF, dfdsfs, fun_name, var_name, anything
    - PYTHON_GEN_REACTIVE   $
    - PYTHON_GEN_ARROW      ->
    - PYTHON_GEN_DECOR      @
    - PYTHON_GEN_PIPE       |
    - PYTHON_GEN_STRING     ...


'''


class MalangeToken:
    '''For Malange tokens.'''
    def __init__(self, token: str = None,
                 value: str = None, ind: int = None) -> None:
        self.token: Optional[str] = token
        self.value: Optional[str] = value
        self.ind:   Optional[int] = ind
    def __call__(self) -> str:
        return f"{self.token}({self.ind}) : {self._value}"

class PyMalangeToken:
    '''For Malange Python tokens.'''
    def __init__(self, token: str = None,
                 value: str = None, ind: int = None) -> None:
        self.token: Optional[str] = token
        self.value: Optional[str] = value
        self.ind:   Optional[int] = ind
    def __call__(self) -> str:
        return f"{self.token}({self.ind}) : {self._value}"
