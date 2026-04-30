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

import os

from .constants import DAT_PATH
from .classes.ars import ARSIndex
from .classes.processing.networkValidator import Networkvalidator

ARS_INDEX = ARSIndex(os.path.join(DAT_PATH, "ARS_Zentren_merged.csv"))
NETWORK_VALIDATOR = Networkvalidator()