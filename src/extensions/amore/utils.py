#############################################################################
# Author: <ana.garcia-tabares@xfel.eu>
# Created on April, 2022
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################


import numpy as np
from pyqtgraph import ColorMap

# ---------------------------------------------------------------------
# Functions associated to the icons plotting
# ---------------------------------------------------------------------


def create_lut(color):
    colors = []
    for i, c in enumerate(color):
        colors.append(tuple([cc * 255 for cc in c] + [1]))
    cmap = ColorMap(np.linspace(0, 1.0, len(colors)), colors)
    lut = cmap.getLookupTable(alpha=False)
    return lut


def display_saved_data(selected_roi):
    selected_roi.setToolTip(
        "Saved: " + str((selected_roi.saved_date)))
