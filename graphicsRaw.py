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
import numpy as np
from PySide2 import QtCore

from PySide2.QtCore import Qt
from PySide2.QtGui import QFontMetrics
from PySide2.QtWidgets import QGraphicsView, QSizePolicy, QVBoxLayout, QLabel, QHBoxLayout, QSlider

from colorConv import temperatureAndTint2RGBMultipliers, RGBMultipliers2TemperatureAndTint, conversionMatrix
from qrangeslider import QRangeSlider
from utils import optionsWidget, UDict, QbLUeSlider

class rawForm (QGraphicsView):
    """
    GUI for postprocessing of raw files
    # cf https://github.com/LibRaw/LibRaw/blob/master/src/libraw_cxx.cpp
    """
    dataChanged = QtCore.Signal(bool)
    @classmethod
    def getNewWindow(cls, targetImage=None, axeSize=500, layer=None, parent=None, mainForm=None):
        wdgt = rawForm(axeSize=axeSize, layer=layer, parent=parent, mainForm=mainForm)
        wdgt.setWindowTitle(layer.name)
        return wdgt

    def __init__(self, targetImage=None, axeSize=500, layer=None, parent=None, mainForm=None):
        super(rawForm, self).__init__(parent=parent)
        self.setStyleSheet('QRangeSlider * {border: 0px; padding: 0px; margin: 0px}')
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setMinimumSize(axeSize, axeSize+200)  # +200 to prevent scroll bars in list Widgets
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.layer = layer
        # get rawpy object
        rawpyObj = layer.parentImage.rawImage
        ###############################################
        # rawMultipliers are used for rawimage postprocessing.
        # Initially, they are taken from raw file.
        ###############################################
        self.rawMultipliers = rawpyObj.camera_whitebalance

        daylight = rawpyObj.daylight_whitebalance
        #self.rawMultipliers = [daylight[i] / multipliers[i] for i in range(3)] + [daylight[1] / multipliers[1]]
        # get Camera RGB - XYZ conversion matrix.
        # From rawpy doc, this matrix is constant for each camera model
        # Last row is zero for RGB cameras and non-zero for different color models (CMYG and so on) : type ndarray of shape (4,3)
        rgb_xyz_matrix = rawpyObj.rgb_xyz_matrix[:3,:]
        rgb_xyz_matrix_inverse = np.linalg.inv(rgb_xyz_matrix)
        # Color_matrix, read from file for some cameras, calculated for others, type ndarray of shape (3,4), seems to be 0.
        # color_matrix = rawpyObj.color_matrix
        #################################
        # Libraw correspondances:
        # rgb_xyz_matrix is libraw cam_xyz
        # camera_whitebalance is libraw cam_mul
        # daylight_whitebalance is libraw pre_mul
        ##################################
        # get temp and tint from rawpy object (as shot values). Base ref. is daylight
        multipliers = [daylight[i] / self.rawMultipliers[i] for i in range(3)]
        self.cameraTemp, self.cameraTint = RGBMultipliers2TemperatureAndTint(*multipliers, rgb_xyz_matrix_inverse)
        # options
        optionList0 = ['Auto Brightness', 'Preserve Highlights', 'Auto Scale']
        self.listWidget1 = optionsWidget(options=optionList0, exclusive=False, changed=lambda: self.dataChanged.emit(True))
        self.listWidget1.checkOption(self.listWidget1.intNames[0])
        optionList1 = ['Auto WB', 'Camera WB', 'User WB']
        self.listWidget2 = optionsWidget(options=optionList1, exclusive=True, changed=lambda: self.dataChanged.emit(True))
        self.listWidget2.checkOption(self.listWidget2.intNames[1])
        self.options = UDict(self.listWidget1.options, self.listWidget2.options)

        # WB sliders
        self.sliderTemp = QbLUeSlider(Qt.Horizontal)
        self.sliderTemp.setStyleSheet("""QSlider::groove:horizontal {margin: 3px; 
                                          background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 blue, stop:1 red);}""")
        self.sliderTemp.setRange(0,130)

        self.sliderTemp.setSingleStep(1)

        self.tempLabel = QLabel()
        self.tempLabel.setText("Temp")

        self.tempValue = QLabel()
        font = self.tempValue.font()
        metrics = QFontMetrics(font)
        w = metrics.width("10000")
        h = metrics.height()
        self.tempValue.setMinimumSize(w, h)
        self.tempValue.setMaximumSize(w, h)
        self.tempValue.setText(str("{:.0f}".format(self.slider2Temp(self.sliderTemp.value()))))

        # temp changed  event handler
        def tempUpdate(value):
            self.tempValue.setText(str("{:.0f}".format(self.slider2Temp(self.sliderTemp.value()))))
            # move not yet terminated or value not modified
            if self.sliderTemp.isSliderDown() or self.slider2Temp(value) == self.tempCorrection:
                return
            self.sliderTemp.valueChanged.disconnect()
            self.sliderTemp.sliderReleased.disconnect()
            self.tempCorrection = self.slider2Temp(self.sliderTemp.value())


            multipliers = temperatureAndTint2RGBMultipliers(self.tempCorrection, self.tintCorrection, rgb_xyz_matrix_inverse)
            self.rawMultipliers = [daylight[i] / multipliers[i] for i in range(3)] + [daylight[1] / multipliers[1]]
            m = min(self.rawMultipliers[:3])
            self.rawMultipliers = [self.rawMultipliers[i] / m for i in range(4)]
            self.dataChanged.emit(True)
            self.sliderTemp.valueChanged.connect(tempUpdate)  # send new value as parameter
            self.sliderTemp.sliderReleased.connect(lambda: tempUpdate(self.sliderTemp.value()))  # signal has no parameter
        self.sliderTemp.valueChanged.connect(tempUpdate)  # send new value as parameter
        self.sliderTemp.sliderReleased.connect(lambda :tempUpdate(self.sliderTemp.value()))  # signal has no parameter

        # tint slider
        self.sliderTint = QbLUeSlider(Qt.Horizontal)
        #self.sliderTint.setStyleSheet(self.sliderTint.styleSheet()+'QSlider::groove:horizontal {background: red;}')
        self.sliderTint.setStyleSheet("""QSlider::groove:horizontal {margin: 3px; 
                                         background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 green, stop:1 magenta);}""")
        self.sliderTint.setRange(0, 150)

        self.sliderTint.setSingleStep(1)

        self.tintLabel = QLabel()
        self.tintLabel.setText("Tint")

        self.tintValue = QLabel()
        font = self.tempValue.font()
        metrics = QFontMetrics(font)
        w = metrics.width("100")
        h = metrics.height()
        self.tintValue.setMinimumSize(w, h)
        self.tintValue.setMaximumSize(w, h)
        self.tintValue.setText(str("{:.0f}".format(self.sliderTint2User(self.sliderTint.value()))))

        # tint change event handler
        def tintUpdate(value):
            self.tintValue.setText(str("{:.0f}".format(self.sliderTint2User(self.sliderTint.value()))))
            # move not yet terminated or value not modified
            if self.sliderTint.isSliderDown() or self.slider2Tint(value) == self.tintCorrection:
                return
            self.sliderTint.valueChanged.disconnect()
            self.sliderTint.sliderReleased.disconnect()
            self.tintCorrection = self.slider2Tint(self.sliderTint.value())
            multipliers = temperatureAndTint2RGBMultipliers(self.tempCorrection, self.tintCorrection, rgb_xyz_matrix_inverse)
            self.rawMultipliers = [daylight[i] / multipliers[i] for i in range(3)] + [daylight[1] / multipliers[1]]
            m = min(self.rawMultipliers[:3])
            self.rawMultipliers = [self.rawMultipliers[i] / m for i in range(4)]
            self.dataChanged.emit(True)
            self.sliderTint.valueChanged.connect(tintUpdate)
            self.sliderTint.sliderReleased.connect(lambda: tintUpdate(self.sliderTint.value()))  # signal has no parameter)
        self.sliderTint.valueChanged.connect(tintUpdate)
        self.sliderTint.sliderReleased.connect(lambda :tintUpdate(self.sliderTint.value()))  # signal has no parameter)

        # exp slider
        self.sliderExp = QbLUeSlider(Qt.Horizontal)
        self.sliderExp.setStyleSheet("""QSlider::groove:horizontal {margin: 3px; 
                                          background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 black, stop:1 white);}""")
        self.sliderExp.setRange(0, 100)

        self.sliderExp.setSingleStep(1)

        self.expLabel = QLabel()
        self.expLabel.setText("Exp")

        self.expValue = QLabel()
        font = self.expValue.font()
        metrics = QFontMetrics(font)
        w = metrics.width("+1.0")
        h = metrics.height()
        self.expValue.setMinimumSize(w, h)
        self.expValue.setMaximumSize(w, h)
        self.expValue.setText(str("{:.1f}".format(self.slider2Exp(self.sliderExp.value()))))

        # exp done event handler
        def expUpdate(value):
            self.expValue.setText(str("{:.1f}".format(self.slider2Exp(self.sliderExp.value()))))
            # move not yet terminated or value not modified
            if self.sliderExp.isSliderDown() or self.slider2Exp(value) == self.expCorrection:
                return
            self.sliderExp.valueChanged.disconnect()
            self.sliderExp.sliderReleased.disconnect()
            # rawpy: expCorrection range is -2.0...3.0 boiling down to exp_shift range 2**(-2)=0.25...2**3=8.0
            self.expCorrection = self.slider2Exp(self.sliderExp.value())
            self.dataChanged.emit(True)
            self.sliderExp.valueChanged.connect(expUpdate)  # send new value as parameter
            self.sliderExp.sliderReleased.connect(lambda: expUpdate(self.sliderExp.value()))  # signal has no parameter
        self.sliderExp.valueChanged.connect(expUpdate)  # send new value as parameter
        self.sliderExp.sliderReleased.connect(lambda: expUpdate(self.sliderExp.value()))  # signal has no parameter

        # brightness slider
        brSlider = QbLUeSlider(Qt.Horizontal)
        brSlider.setRange(0, 150)

        self.sliderExp.setSingleStep(1)

        brSlider.setStyleSheet("""QSlider::groove:horizontal {margin: 3px; 
                                          background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 black, stop:1 white);}""")

        self.sliderBrightness = brSlider
        brLabel = QLabel()
        brLabel.setText("Brightness")

        self.brValue = QLabel()
        font = self.expValue.font()
        metrics = QFontMetrics(font)
        w = metrics.width("+99")
        h = metrics.height()
        self.brValue.setMinimumSize(w, h)
        self.brValue.setMaximumSize(w, h)
        self.brValue.setText(str("{:.1f}".format(self.brSlider2User(self.sliderBrightness.value()))))

        # brightness done event handler
        def brUpdate(value):
            self.brValue.setText(str("{:.1f}".format(self.brSlider2User(self.sliderBrightness.value()))))
            # move not yet terminated or value not modified
            if self.sliderBrightness.isSliderDown() or self.slider2Br(value) == self.brCorrection:
                return
            self.sliderBrightness.valueChanged.disconnect()
            self.sliderBrightness.sliderReleased.disconnect()
            self.brCorrection = self.slider2Br(self.sliderBrightness.value())
            self.dataChanged.emit(True)
            self.sliderBrightness.sliderReleased.connect(lambda: brUpdate(self.sliderBrightness.value()))
            self.sliderBrightness.valueChanged.connect(brUpdate)  # send new value as parameter
        self.sliderBrightness.valueChanged.connect(brUpdate)  # send new value as parameter
        self.sliderBrightness.sliderReleased.connect(lambda: brUpdate(self.sliderBrightness.value()))

        # contrast slider
        self.sliderCont = QbLUeSlider(Qt.Horizontal)
        self.sliderCont.setStyleSheet("""QSlider::groove:horizontal {margin: 3px;
                                          background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 grey, stop:1 white);}""")
        self.sliderCont.setRange(0, 20)

        self.sliderCont.setSingleStep(1)

        self.contLabel = QLabel()
        self.contLabel.setText("Contrast")

        self.contValue = QLabel()
        font = self.contValue.font()
        metrics = QFontMetrics(font)
        w = metrics.width("100")
        h = metrics.height()
        self.contValue.setMinimumSize(w, h)
        self.contValue.setMaximumSize(w, h)
        self.contValue.setText(str("{:.0f}".format(self.slider2Cont(self.sliderCont.value()))))

        # cont done event handler
        def contUpdate(value):
            self.contValue.setText(str("{:.0f}".format(self.slider2Cont(self.sliderCont.value()))))
            # move not yet terminated or value not modified
            if self.sliderCont.isSliderDown() or self.slider2Cont(value) == self.tempCorrection:
                return
            self.sliderCont.valueChanged.disconnect()
            self.sliderCont.sliderReleased.disconnect()
            self.contCorrection = self.slider2Cont(self.sliderCont.value())
            self.contValue.setText(str("{:+d}".format(self.contCorrection)))
            self.dataChanged.emit(False)
            self.sliderCont.valueChanged.connect(contUpdate)  # send new value as parameter
            self.sliderCont.sliderReleased.connect(lambda: contUpdate(self.sliderCont.value()))  # signal has no parameter
        self.sliderCont.valueChanged.connect(contUpdate)  # send new value as parameter
        self.sliderCont.sliderReleased.connect(lambda: contUpdate(self.sliderCont.value()))  # signal has no parameter

        # noise reduction slider
        self.sliderNoise = QbLUeSlider(Qt.Horizontal)
        self.sliderNoise.setStyleSheet("""QSlider::groove:horizontal {margin: 3px; 
                                         background: blue /*qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 blue, stop:1 red)*/;}""")
        self.sliderNoise.setRange(0, 20)

        self.sliderNoise.setSingleStep(1)

        noiseLabel = QLabel()
        #noiseLabel.setFixedSize(110, 20)
        noiseLabel.setText("Noise Red.")

        self.noiseValue = QLabel()
        font = self.noiseValue.font()
        metrics = QFontMetrics(font)
        w = metrics.width("1000")
        h = metrics.height()
        self.noiseValue.setMinimumSize(w, h)
        self.noiseValue.setMaximumSize(w, h)
        self.noiseValue.setText(str("{:.0f}".format(self.slider2Noise(self.sliderNoise.value()))))

        # noise done event handler
        def noiseUpdate(value):
            self.noiseValue.setText(str("{:.0f}".format(self.slider2Noise(self.sliderNoise.value()))))
            # move not yet terminated or value not modified
            if self.sliderNoise.isSliderDown() or self.slider2Noise(value) == self.noiseCorrection:
                return
            self.sliderNoise.valueChanged.disconnect()
            self.sliderNoise.sliderReleased.disconnect()
            self.noiseCorrection = self.slider2Noise(self.sliderNoise.value())
            self.noiseValue.setText(str("{:+d}".format(self.slider2Noise(self.sliderNoise.value()))))
            self.dataChanged.emit(False)
            self.sliderNoise.valueChanged.connect(noiseUpdate)  # send new value as parameter
            self.sliderNoise.sliderReleased.connect(lambda: noiseUpdate(self.sliderNoise.value()))  # signal has no parameter
        self.sliderNoise.valueChanged.connect(noiseUpdate)  # send new value as parameter
        self.sliderNoise.sliderReleased.connect(lambda: noiseUpdate(self.sliderNoise.value()))  # signal has no parameter

        # saturation slider
        self.sliderSat = QbLUeSlider(Qt.Horizontal)
        self.sliderSat.setStyleSheet("""QSlider::groove:horizontal {margin: 3px; 
                                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #999999, stop:1 red);}""")
        self.sliderSat.setRange(0, 100)

        self.sliderSat.setSingleStep(1)

        satLabel = QLabel()
        satLabel.setText("Sat")

        self.satValue = QLabel()
        font = self.satValue.font()
        metrics = QFontMetrics(font)
        w = metrics.width("100")
        h = metrics.height()
        self.satValue.setMinimumSize(w, h)
        self.satValue.setMaximumSize(w, h)
        self.satValue.setText(str("{:+d}".format(self.slider2Sat(self.sliderSat.value()))))

        # sat done event handler
        def satUpdate(value):
            self.satValue.setText(str("{:+d}".format(self.slider2Sat(self.sliderSat.value()))))
            # move not yet terminated or value not modified
            if self.sliderSat.isSliderDown() or self.slider2Sat(value) == self.satCorrection:
                return
            self.sliderSat.valueChanged.disconnect()
            self.sliderSat.sliderReleased.disconnect()
            self.satCorrection = self.slider2Sat(self.sliderSat.value())
            #self.satValue.setText(str("{:+d}".format(slider2Sat(self.sliderSat.value()))))
            self.dataChanged.emit(False)
            self.sliderSat.valueChanged.connect(satUpdate)  # send new value as parameter
            self.sliderSat.sliderReleased.connect(lambda: satUpdate(self.sliderSat.value()))  # signal has no parameter
        self.sliderSat.valueChanged.connect(satUpdate)  # send new value as parameter
        self.sliderSat.sliderReleased.connect(lambda: satUpdate(self.sliderSat.value()))  # signal has no parameter

        # data changed event handler
        def updateLayer(invalidate):
            if invalidate:
               self.layer.postProcessCache = None
            self.enableSliders()
            self.layer.applyToStack()
            self.layer.parentImage.onImageChanged()
        self.dataChanged.connect(updateLayer)
        self.setStyleSheet("QListWidget, QLabel {font : 7pt;}")

        #layout
        l = QVBoxLayout()
        l.setContentsMargins(8, 8, 8, 8)  # left, top, right, bottom
        l.setAlignment(Qt.AlignBottom)
        hl1 = QHBoxLayout()
        hl1.addWidget(self.expLabel)
        hl1.addWidget(self.expValue)
        hl1.addWidget(self.sliderExp)
        l.addWidget(self.listWidget1)
        l.addWidget(self.listWidget2)
        hl2 = QHBoxLayout()
        hl2.addWidget(self.tempLabel)
        hl2.addWidget(self.tempValue)
        hl2.addWidget(self.sliderTemp)
        hl3 = QHBoxLayout()
        hl3.addWidget(self.tintLabel)
        hl3.addWidget(self.tintValue)
        hl3.addWidget(self.sliderTint)
        hl4 = QHBoxLayout()
        hl4.addWidget(self.contLabel)
        hl4.addWidget(self.contValue)
        hl4.addWidget(self.sliderCont)

        hl8 = QHBoxLayout()
        hl8.addWidget(brLabel)
        hl8.addWidget(self.brValue)
        hl8.addWidget(self.sliderBrightness)
        hl7 = QHBoxLayout()
        hl7.addWidget(satLabel)
        hl7.addWidget(self.satValue)
        hl7.addWidget(self.sliderSat)
        hl5 = QHBoxLayout()
        hl5.addWidget(noiseLabel)
        hl5.addWidget(self.noiseValue)
        hl5.addWidget(self.sliderNoise)
        l.addLayout(hl2)
        l.addLayout(hl3)
        l.addLayout(hl1)
        l.addLayout(hl4)
        l.addLayout(hl8)
        l.addLayout(hl7)
        l.addLayout(hl5)
        l.addStretch(1)
        self.setLayout(l)
        self.adjustSize()
        self.setDefaults()

    def slider2Temp(self, v):
        return 2000 + v * v

    def temp2Slider(self, T):
        return np.sqrt(T - 2000)

    def slider2Tint(self, v):
        return 0.1 + 0.0125 * v  # 0.2 + 0.0125 * v  # wanted range : 0.2...2.5
        # coeff = (self.tempCorrection / 4000 - 1) * 1.2 # experimental formula
        # eturn coeff + 0.01*v

    def tint2Slider(self, t):
        return (t - 0.1) / 0.0125
        # coeff = (self.tempCorrection / 4000 - 1) * 1.2 # experimental formula
        # return (t-coeff)/0.01
        # displayed value

    def sliderTint2User(self, v):
        return v - 75  # ((slider2Tint(v) - 1)*100)

    def slider2Exp(self, v):
        return v / 20.0 - 2.0

    def exp2Slider(self, e):
        return round((e + 2.0) * 20.0)

    def slider2Cont(self, v):
        return v

    def cont2Slider(self, e):
        return e

    def slider2Br(self, v):
        return v/50

    def br2Slider(self, e):
        return int(round(50.0 * e))

    def brSlider2User(self, v):
        return (v - 50)

    def slider2Noise(self, v):
        return v

    def noise2Slider(self, e):
        return e

    def slider2Sat(self, v):
        return v - 50  # np.math.pow(10, v / 50)

    def sat2Slider(self, e):
        return e + 50  # 50 * np.math.log10(e)

    def enableSliders(self):
        useUserWB = self.listWidget2.options["User WB"]
        useUserExp = not self.listWidget1.options["Auto Brightness"]
        self.sliderTemp.setEnabled(useUserWB)
        self.sliderTint.setEnabled(useUserWB)
        self.sliderExp.setEnabled(useUserExp)
        self.tempValue.setEnabled(self.sliderTemp.isEnabled())
        self.tintValue.setEnabled(self.sliderTint.isEnabled())
        self.expValue.setEnabled(self.sliderExp.isEnabled())
        self.tempLabel.setEnabled(self.sliderTemp.isEnabled())
        self.tintLabel.setEnabled(self.sliderTint.isEnabled())
        self.expLabel.setEnabled(self.sliderExp.isEnabled())

    def setDefaults(self):
        self.listWidget1.unCheckAll()
        self.listWidget2.unCheckAll()
        self.listWidget1.checkOption(self.listWidget1.intNames[0])
        self.listWidget2.checkOption(self.listWidget2.intNames[1])
        self.enableSliders()
        self.tempCorrection = self.cameraTemp
        self.tintCorrection = self.cameraTint
        self.expCorrection = 0.0
        self.contCorrection = 0.0
        self.noiseCorrection = 0
        self.satCorrection = 0.5
        self.brCorrection = 1.0
        self.sliderTemp.setValue(round(self.temp2Slider(self.tempCorrection)))
        self.sliderTint.setValue(round(self.tint2Slider(self.tintCorrection)))
        self.sliderExp.setValue(self.exp2Slider(self.expCorrection))
        self.sliderCont.setValue(self.cont2Slider(self.contCorrection))
        self.sliderBrightness.setValue(self.br2Slider(self.brCorrection))
        self.sliderNoise.setValue(self.noise2Slider(self.noiseCorrection))
        self.sliderSat.setValue(self.sat2Slider(self.satCorrection))

    def writeToStream(self, outStream):
        layer = self.layer
        outStream.writeQString(layer.actionName)
        outStream.writeQString(layer.name)
        outStream.writeQString(self.listWidget1.selectedItems()[0].text())
        outStream.writeInt32(self.sliderExp.value())
        return outStream

    def readFromStream(self, inStream):
        actionName = inStream.readQString()
        name = inStream.readQString()
        sel = inStream.readQString()
        temp = inStream.readInt32()
        for r in range(self.listWidget1.count()):
            currentItem = self.listWidget1.item(r)
            if currentItem.text() == sel:
                self.listWidget.select(currentItem)
        self.sliderExp.setValue(temp)
        self.update()
        return inStream