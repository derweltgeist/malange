from malange_core.internal.manager.config import MalangeModeType

MODE    = MalangeModeType.DEBUG
PLUGINS = {}

class GATEWAY:
    pass

class MIDDLEWARE:
    pass

class ENGINE:
    EXECUTIVES = {
        "style"  : {
            "lang" : {
                "css" : MalangeCSSExecutive
            }
        }
    }
