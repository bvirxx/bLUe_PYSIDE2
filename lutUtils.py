"""
This File is part of bLUe software.

Copyright (C) 2017  Bernard Virot <bernard.virot@libertysurf.fr>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as
published by the Free Software Foundation, version 3.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Lesser General Lesser Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
#####################################
# Initializes LUT3D related constants
#####################################

import numpy as np
from bLUeCore.bLUeLUT3D import LUT3D

LUTSIZE = LUT3D.defaultSize
LUT3DIdentity = LUT3D(None, size=LUTSIZE)
LUTSTEP = LUT3DIdentity.step
LUT3D_ORI = LUT3DIdentity.LUT3DArray
__a, __b, __c, __d = LUT3D_ORI.shape
LUT3D_SHADOW = np.zeros((__a, __b, __c, __d+1))
LUT3D_SHADOW[:,:,:,:3] = LUT3D_ORI
