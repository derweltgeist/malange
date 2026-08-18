'''

    malange_core.api.log

    Provides the special logging API of Malange.

    How it works is:
    - During locking (stored in Logger.LOCK), Logger is still in the configuration phase.
    - That means setting up basicConfig, and the only valid logger name is malange_core
    - During locking, other components are not permitted to run. Thus you must init with no name.
    - Then, you must call the instance to feed the project name. The data will be stored in Logger.NAME
    - After that, self.conf() is called with argument of the log level in accordance to the mode.
    - If VERBOSE the level is logging.INFO. If NORMAL the level is logging.WARNING. If DEBUG the level
        is logging.DEBUG
    - After that, self.conf() will disable lock.
    - Post-locking, if you init with no name, we assume you to be a malange project. But there can
        only be one chance to init. The moment you try to init again, it will throw error. The bool
        is Logger.PROJ.
    - 

'''

import sys
import logging

from typing import Literal, Optional, TYPE_CHECKING

if TYPE_CHECKING: # To prevent circular imports, only import for type checking.
    from malange_core.internal.manager.project import MalangeProject

class Logger:
    '''Logging API for Malange.'''

    # BOOTSTRAP SYSTEM
    LOCK    : bool                     = True   # Check if the Logger is locked or not.
    PROJ    : bool                     = False  # Check if project logger has been initialized or not.
    PLUGINS : dict[str, bool]          = {}     # Check if plugin logger has been initialized or not.
    def __init__(self, name: str = ""):
        '''Set up locking phase and system of logger registration.'''
        if Logger.LOCK: # During locking, that means Logger is still in the configuration phase.
            logging.basicConfig(
                level=logging.WARNING,
                format="%(asctime)s [%(levelname)s] %(message)s"
            )
            if name == "": # As such, the only valid component is the core.
                self.name = "malange_mgr"
            else:
                self.error("The only component allowed during logging LOCK is MGR.")
        else: # But if locking is no longer enabled, anything can run.
            if name == "": # If no name is provided, auto-assume malange project.
                if Logger.PROJ:
                    self.critical("Project logger has been initialized.")
                self.name = "malange_proj"
                Logger.PROJ = True # You can't initialize again.
            else: # If name is provided, auto-assume malange plugin.
                if name in Logger.PLUGINS: # Check if the plugin is installed.
                    if not Logger.PLUGINS[name]: # Check if the plugin has been initialized.
                        self.name = name
                    else:
                        self.critical(f"Plugin logger by the name of {name} has been initialized.")
                else:
                    self.critical(
    f"Plugin logger by the name of {name} does not exist in the PLUGINS project config entity.") 
    def conf(self, log: Literal[10, 20, 30, 40, 50]) -> None:
        '''Configure the logger to exit locking phase with proper configuration.'''
        if Logger.LOCK: # If LOCK is True, set up basicConfig again
            logging.basicConfig(
                level=log,
                format="%(asctime)s [%(levelname)s] %(message)s"
            )
            Logger.LOCK = False
        else:
            self.error("self.conf of Logger can only be run during locking phase.")
    def plugin(self, name: list[str]):
        '''Configure the logger list of plugins.'''
        if Logger.LOCK:
            Logger.PLUGINS = dict.fromkeys(name, False)
        else:
            self.error("self.plugin of Logger can only be run during locking phase.")

    # LOGGING SYSTEM
    def debug(self, msg: str):
        '''For debug logging.'''
        logging.debug(f"{self.name} : {msg}")
    def info(self, msg: str):
        '''For info logging.'''
        logging.info(f"{self.name} : {msg}")    
    def warning(self, msg: str):
        '''For warning logging.'''
        logging.warning(f"{self.name} : {msg}")
    def error(self, msg: str):
        '''For error logging.'''
        logging.error(f"{self.name} : {msg}")
    def critical(self, msg: str, error: Optional[Exception] = None):
        '''For critical logging.'''
        has_exception: bool = sys.exc_info()[0] is not None
        logging.critical(f"{self.name} : {msg}", exc_info=has_exception)
        if error is None: # If no error is passed.
            raise
        elif isinstance(error, Exception): # If error is passed.
            raise error()
        else: # If error is not an exception.
            logging.critical(f"{self.name} : Passed error object is not an exception.", exc_info=has_exception)
            raise
