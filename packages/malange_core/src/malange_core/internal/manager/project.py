'''

malange_core.internal.amanger.project

This contains code that a Malange project will call to initialize
the system, this mostly performs component registration. The rest
are done by the trio components: Engine, middleware, and gateway.

'''

import sys
import types
import logging
import importlib
import importlib.util

from typing import Union
from importlib.machinery import ModuleSpec

from malange_core.api.log import MalangeLogger
from malange_core.internal.engine import MalangeEngine
from malange_core.internal.manager.config import (MalangePluginType,
                                                  MalangeModeType, MalangePluginConfigNull)
from malange_core.internal.manager import MalangeManagerLogger

class MalangeProject:
    def __call__(self, conf: types.ModuleType, pwd: str):
        self.__conf   : types.ModuleType = conf            # Save the configuration module.
        self.__pwd    : str              = pwd             # Working directory.
        self.__log    : MalangeLogger    = MalangeLogger() # Register log for Malange Core first.
        # Register components.
        log = self.__mode_register() # Register mode (debug / verbose / normal)
        self.__plug_register()       # Register plugins.
        self.__log.conf(log)         # Disable locking phase.
        self.__role_register()       # Register roles.
        # Initialize components.
        self.__engine: MalangeEngine = MalangeEngine(self)

    # Retrive configurations.
    def raw_module(self, conf: str) -> any:
        '''Retrive raw configurations.'''
        return self.__conf.__getattr__(conf)
    def import_conf(self, conf: str) -> types.ModuleType:
        '''Retrive configurations as import statements.'''
        return importlib.import_module(self.__conf.__getattr__(conf))
    def retrive_pwd(self) -> str:
        return self.__pwd

    # Register methods.
    def __mode_register(self) -> int:
        '''Retrive DEBUG conf and set logging configurations.'''
        try:
            self.MODE: str = self.__conf.MODE
        except AttributeError:
            self.__log.critical("MODE is not defined as a config entity.")
        # Check the values.
        if self.MODE == MalangeModeType.DEBUG:
            log = logging.DEBUG
        elif self.MODE == MalangeModeType.VERBOSE:
            log = logging.INFO
        elif self.MODE == MalangeModeType.NORMAL:
            log = logging.WARN
        else:
            self.__log.critical("Invalid value of MODE, should be DEBUG, VERBOSE, or NORMAL.")
        # Set MalangeManagerLogger, that will function as the malange_mgr logger.
        MalangeManagerLogger = self.__log
        return log
    def __plug_register(self):
        '''Register plugins.'''
        try:
            self.PLUGINS: dict[str, Union[
                MalangePluginType.PACK,
                MalangePluginType.PROJ,
                MalangePluginType.DIRE
            ]] = self.__conf.PLUGINS
        except AttributeError:
            self.__log.critical("PLUGINS is not defined as a config entity.")

        if isinstance(self.PLUGINS, dict):
            # Variable to store the plugin modules.
            self.__plugin      : dict[str, types.ModuleType] = {}
            # Variable to store the plugin configurations.
            self.__plugin_conf : dict[str, dict[str, any]]   = {}
            for index, (key, value) in enumerate(self.PLUGINS.items()):
                # Check the key.
                if not isinstance(key, str):
                    self.__log.critical(f"Key of index {index} of PLUGINS is not a string.")
                # Attempt to import (and check the value)
                if value == MalangePluginType.PACK:
                    try:
                        plugin: types.ModuleType = importlib.import_module(key)
                    except ImportError:
                        self.__log.critical(f"Plugin index {index} is not found as a package import.")
                elif value == MalangePluginType.PROJ:
                    try:
                        directory: str = f"{self.__pwd}/plugins/{value}"
                        spec: ModuleSpec = importlib.util.spec_from_file_location("plugin", directory)
                        plugin: types.ModuleType = importlib.util.module_from_spec(spec)
                        sys.modules["plugin"] = plugin
                        spec.loader.exec_module(plugin)
                    except ImportError:
                        self.__log.critical(f"Plugin index {index} is not found as a package import.")
                elif value == MalangePluginType.DIRE:
                    try:
                        directory: str = value
                        spec: ModuleSpec = importlib.util.spec_from_file_location("plugin", directory)
                        plugin: types.ModuleType = importlib.util.module_from_spec(spec)
                        sys.modules["plugin"] = plugin
                        spec.loader.exec_module(plugin)
                    except ImportError:
                        self.__log.critical(f"Plugin index {index} is not found as a package import.")
                else:
                    self.__log.critical(f"Value of index {index} of PLUGINS is not valid.")
                # Get the name.
                try:
                    name = plugin.config.NAME
                except AttributeError:
                    self.__log.critical(f"Plugin index {index} has no name.")
                if not isinstance(name, str):
                    self.__log.critical(f"Plugin index {index} has an invalid type for it's name.")
                # Set the plugin in self.__plugin with name as key.
                if name in self.__plugin:
                    self.__log.critical(f"Duplicate plugin name is detected at plugin index {index}")
                else:
                    self.__plugin[name] = plugin
                self.__log(self.__plugin.keys()) # Configure plugin loggers.
                # Set the plugin configuration in self.__plugin_conf with key being the plugin name
                # and the value being a dictionary full of the list of configs the plugin requests.
                try: # Obtain the requested config that the plugin wants, inside plugin.config.ENTITIES
                    plugin_conf_req: dict[str, any] = plugin.config.ENTITIES
                except AttributeError:
                    plugin_conf_req: dict[str, any] = {} # We assume the plugin does not need any config.
                formatted_plugin_conf: dict[str, any] = {}
                # Entity = config name, ent_type = the type of the value of the config entity.
                for i, (entity, ent_type) in enumerate(plugin_conf_req.items()):
                    if isinstance(entity, str): # Entity must be a str.
                        self.CRITICAL(f"Plugin {name} has config index {i} with non-str key.")
                    if entity[-1] == "*": # This indicates the config is totally optional.
                        try: # Check if the config exists.
                            value: any = getattr(self.__conf, name)[entity[:-1]]
                        except AttributeError or KeyError:
                            value: MalangePluginConfigNull = MalangePluginConfigNull
                    else: # The config is not optional.
                        try: # Check if the config exists.
                            value: any = getattr(self.__conf, name)[entity]
                        except AttributeError:
                            self.CRITICAL(f"Plugin {name} has its config class undefined.")
                        except KeyError:
                            self.CRITICAL(f"Plugin {name} has config {entity} which is not defined.")                            
                    if isinstance(value, ent_type): # Check the config value.
                        formatted_plugin_conf[entity] = value
                    else:
                        self.CRITICAL(f"Plugin {name} has config {entity} whose value is invalid.")
                self.__plugin_conf[name] = formatted_plugin_conf # Add it up to the self.__plugin_conf
        else:
            self.__log.critical("PLUGINS is not a dictionary.")
    def __role_register(self):
        '''Register the three important configs for role of plugins: GATEWAY, MIDDLE, and ENGINE.'''
        try:
            self.GATEWAY = self.__conf.GATEWAY
        except AttributeError:
            self.__log.critical("GATEWAY is not defined as a config entity.")
        try:
            self.MIDDLEWARE = self.__conf.MIDDLEWARE
        except AttributeError:
            self.__log.critical("MIDDLEWARE is not defined as a config entity.")
        try:
            self.ENGINE = self.__conf.ENGINE
        except AttributeError:
            self.__log.critical("ENGINE is not defined as a config entity.")
