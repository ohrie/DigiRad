# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 Vision Velo GmbH

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""

from typing import Optional
from datetime import datetime

from .ars import ARSCode

class ProcessingConfig:
    DefaultProjectName = "DigiRad"

    def __init__(self):
        self.projectName = ProcessingConfig.DefaultProjectName
        self.arsCode = None
    
    def setARSCode(self, arsCode: Optional[ARSCode]):
        self.arsCode = arsCode
        dt = datetime.today().strftime('%Y-%m-%d-T%H-%M')
        if not arsCode:
            self.projectName = f"{ProcessingConfig.DefaultProjectName}_{dt}"
        else:
            self.projectName = f"{arsCode.name}_{dt}"