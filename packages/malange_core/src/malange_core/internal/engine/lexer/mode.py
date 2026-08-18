'''
    malange_core.internal.engine.lexer.mode

    Storing the default modes (DefaultModes) and LexerMode
    to manage these modes. 
'''

from enum import Enum, auto

class DefaultModes(Enum):
    # Non-affliated components.
    NORMAL_CODE   = auto() # No detection.
    NORMAL_COMME  = auto() # <!-- ... should end with -->
    NORMAL_STR    = auto() # " ... " or ' ... ' or """ ... """ or ''' ... ''' or ` ... `
    # HTML and Malange tags.
    TAG_HTML      = auto() # < ... should end with > or />
    TAG_MALANGE   = auto() # </ ... should end with >
    # Python: Any Python code.
    PYTHON_CODE   = auto() # Generic Python code.
    PYTHON_COMME  = auto() # # .... should end with newline.
    # Javascript: JS Script is not taken care.
    JS_CODE       = auto()  # JS code wrapped in <script>
    JS_COMME      = auto()  # // .... // or /* .... */
    # CSS: CSS is also not handled (not yet)
    CSS_CODE      = auto()  # Any style code wrapped in <style>, right now CSS only.
    CSS_COMME     = auto()  # /* ... *

class LexerMode:
    def __init__(self):
        self.modes = {}
        self.__process()
    def __process(self, classes):
        for a_class in [DefaultModes].append(classes):
            self.modes[a_class.__name__] = a_class
