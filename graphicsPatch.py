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
from PySide2.QtWidgets import QGraphicsView, QSizePolicy, QVBoxLayout, QHBoxLayout

from utils import optionsWidget


class patchForm (QGraphicsView):
    @classmethod
    def getNewWindow(cls, targetImage=None, axeSize=500, layer=None, parent=None, mainForm=None):
        wdgt = patchForm(targetImage=targetImage, axeSize=axeSize, layer=layer, parent=parent, mainForm=mainForm)
        wdgt.setWindowTitle(layer.name)
        """
        pushButton = QPushButton('apply', parent=wdgt)
        hLay = QHBoxLayout()
        wdgt.setLayout(hLay)
        hLay.addWidget(pushButton)
        pushButton.clicked.connect(lambda: wdgt.execute())
        """
        return wdgt

    def __init__(self, targetImage=None, axeSize=500, layer=None, parent=None, mainForm=None):
        super(patchForm, self).__init__(parent=parent)
        self.targetImage = targetImage
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setMinimumSize(axeSize, axeSize)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.img = targetImage
        self.layer = layer
        self.mainForm = mainForm
        self.onUpdateFilter = lambda *args: 0

        l = QVBoxLayout()
        l.setAlignment(Qt.AlignBottom)

        # options
        options = ['Unsharp Mask', 'Sharpen', 'Gaussian Blur']

        self.options={}
        for op in options:
            self.options[op] = False
        self.listWidget1 = optionsWidget(options=options, exclusive=True)
        sel = options[0]
        self.listWidget1.select(self.listWidget1.items[sel])
        self.options[sel] = True
        self.defaultRadius = 1
        self.defaultAmount = 50

        # select event handler
        def onSelect1(item):
            for key in self.options:
                self.options[key] = item is self.listWidget1.items[key]
                if self.options[key]:
                    selkey = key

        hl = QHBoxLayout()

        l.addLayout(hl)

        l.setContentsMargins(20, 0, 20, 25)  # left, top, right, bottom

        self.setLayout(l)



        # set initial selection to unsharp mask
        item = self.listWidget1.items[options[0]]
        item.setCheckState(Qt.Checked)
        self.listWidget1.select(item)
        l.addWidget(self.listWidget1)
