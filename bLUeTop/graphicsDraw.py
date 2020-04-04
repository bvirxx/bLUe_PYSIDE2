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
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QPushButton, QVBoxLayout, QHBoxLayout, QSlider, QLabel

from bLUeGui.graphicsForm import baseForm


class drawForm (baseForm):
    """
    Drawing form
    """
    @classmethod
    def getNewWindow(cls, targetImage=None, axeSize=200, layer=None, parent=None):
        wdgt = drawForm(targetImage=targetImage, axeSize=axeSize, layer=layer, parent=parent)
        wdgt.setWindowTitle(layer.name)
        return wdgt

    def __init__(self, targetImage=None, axeSize=500, layer=None, parent=None):
        super().__init__(layer=layer, targetImage=targetImage, parent=parent)
        self.options = None
        pushButton1 = QPushButton(' Undo ')
        pushButton1.adjustSize()
        pushButton2 = QPushButton(' Redo ')
        pushButton2.adjustSize()

        pushButton1.clicked.connect(self.undo)
        pushButton2.clicked.connect(self.redo)

        spacingSlider = QSlider(Qt.Horizontal)
        spacingSlider.setObjectName('spacingSlider')
        spacingSlider.setRange(1,60)
        spacingSlider.setTickPosition(QSlider.TicksBelow)
        spacingSlider.setSliderPosition(10)
        spacingSlider.sliderReleased.connect(self.parent().label.brushUpdate)
        self.spacingSlider = spacingSlider

        jitterSlider = QSlider(Qt.Horizontal)
        jitterSlider.setObjectName('jitterSlider')
        jitterSlider.setRange(0, 100)
        jitterSlider.setTickPosition(QSlider.TicksBelow)
        jitterSlider.setSliderPosition(0)
        jitterSlider.sliderReleased.connect(self.parent().label.brushUpdate)
        self.jitterSlider = jitterSlider

        # layout
        l = QVBoxLayout()
        l.setAlignment(Qt.AlignTop)
        hl = QHBoxLayout()
        hl.setAlignment(Qt.AlignHCenter)
        hl.addWidget(pushButton1)
        hl.addWidget(pushButton2)
        l.addLayout(hl)
        l.addWidget(QLabel('Brush Dynamics'))
        hl1 = QHBoxLayout()
        hl1.addWidget(QLabel('Spacing'))
        hl1.addWidget(spacingSlider)
        l.addLayout(hl1)
        hl2 = QHBoxLayout()
        hl2.addWidget(QLabel('Jitter'))
        hl2.addWidget(jitterSlider)
        l.addLayout(hl2)
        self.setLayout(l)
        self.adjustSize()

        self.setDefaults()
        self.setWhatsThis(
                        """
                        <b>Drawing :</b><br>
                          Choose a brush family, flow, hardness and opacity.
                        """
                        )  # end of setWhatsThis

    def setDefaults(self):
        try:
            self.dataChanged.disconnect()
        except RuntimeError:
            pass
        self.dataChanged.connect(self.updateLayer)

    def updateLayer(self):
        """
        dataChanged slot
        """
        l = self.layer
        # l.tool.setBaseTransform()
        l.applyToStack()
        l.parentImage.onImageChanged()

    def undo(self):
        try:
            self.layer.sourceImg = self.layer.history.undo(saveitem=self.layer.sourceImg.copy()).copy()  # copy is mandatory
            self.updateLayer()
        except ValueError:
            pass

    def redo(self):
        try:
            self.layer.sourceImg = self.layer.history.redo().copy()  # copy is mandatory
            self.updateLayer()
        except ValueError:
            pass

    def reset(self):
        self.layer.tool.resetTrans()
