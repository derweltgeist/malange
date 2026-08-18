from enum import Enum, auto

class MalangePluginType(Enum):
    PACK = auto()
    PROJ = auto()
    DIRE = auto()

class MalangeModeType(Enum):
    NORMAL  = auto()
    VERBOSE = auto()
    DEBUG   = auto()

class MalangePluginConfigNull:
    pass
