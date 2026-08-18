'''

malange_core.internal.manager

This contains all files regarding the machinary to handle registration
of all components (plugins, gateway, engine, manager) plus loading
configurations.

'''

from typing import Optional

from malange_core.api.log import Logger

MalangeManagerLogger: Optional[Logger] = None
