'''

    malange.transpiler.tokenizer.token

    Manages the tokenization of Malange blocks and HTML elements.

    The list of tokens that will be obtained are:

    - MALANGE_BRAC_OPEN         [, ]
    - MALANGE_BRAC_CLOSE        [/, ]
    - MALANGE_BLOCK_KEYWORD     script, for, in, while, if, elif, else, switch, case, default
    - MALANGE_INJ_OPEN          ${
    - MALANGE_INJ_CLOSE         }
    - MALANGE_PYTHON_OPEN       ...
    - MALANGE_PYTHON_CLOSE      ...
    - MALANGE_REACT_BIND        $
    - MALANGE_REACT_KEYWORD     ...
    - MALANGE_EVENT_LIS         @
    - MALANGE_EVENT_KEYWORD     ...
    - MALANGE_WRAP_OPEN         {
    - MALANGE_WRAP_CLOSE        }

    - HTML_TAG_OPEN             <, >
    - HTML_TAG_CLOSE            </, >
    - HTML_BLOCK_KEYWORD        script, h1, etc.
    - HTML_ATTR_NAME            type, class, id, etc
    - HTML_ATTR_VALUE           ...
    - HTML_JS_OPEN              ...
    - HTML_JS_CLOSE             ...

    - OTHER_EQUAL_SIGN          =
    - OTHER_END_LINE            lf, cr, lf-cr, cr-lf are supported.
    - OTHER_END_FILE            Self-explainatory.

'''


class MalangeToken:
    def __init__(self, token: str, value: str):
        self.token: str = token
        self.value: str = value
