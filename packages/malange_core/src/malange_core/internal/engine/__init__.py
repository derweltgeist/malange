'''

malange_core.internal.engine

This contains all files regarding the machinary to handle engines.
- Lexer base class and systems to manage it.
- Parser to construct a full AST from it.

'''

from typing import TYPE_CHECKING

from malange_core.internal.engine.executive import MalangeExecutive

if TYPE_CHECKING: # To prevent circular imports, only import for type checking.
    from malange_core.internal.manager.project import MalangeProject

class MalangeEngine:
    def __init__(self, project: MalangeProject):
        self.__proj: MalangeProject = project
        self.__conf                 = project.ENGINE
        self.__log                  = project.log
        self.__run()
    def __run(self):
        try:
            self.__exec: dict[str, MalangeExecutive] = self.__conf.EXECUTIVES
        except AttributeError:
            self.__log.critical("EXECUTIVES is not found as an attr of ENGINE config entity.")
