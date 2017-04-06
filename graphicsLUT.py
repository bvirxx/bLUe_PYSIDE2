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

import sys

from PySide.QtCore import QRect
from PySide.QtGui import QApplication, QPainter, QWidget
from PySide.QtGui import QGraphicsView, QGraphicsScene, QGraphicsPathItem , QPainterPath, QPainterPathStroker, QPen, QBrush, QColor, QPixmap, QMainWindow, QLabel, QSizePolicy
from PySide.QtCore import Qt, QPoint, QPointF, QRectF
import numpy as np
from PySide.QtGui import QPolygonF

from colorModels import hueSatModel
from spline import cubicSplineCurve

strokeWidth = 3
controlPoints =[]
computeControlPoints = True

def buildLUT(curve):
    """
    Build the LUT from a list of QPOINTF objects, representing
    a curve. The LUT values are interpolated between consecutive curve points.
    x-coordinates of points are assumed to be sorted in ascending order.
    y-coordinates of points are flipped to reflect y-axis orientation.
    :param curve: list of QPOINTF objects
    :return: list of 256 integer values, between 0 and 255.
    """
    # add sentinels
    S1 = QPointF(-1, curve[0].y())
    S2 = QPointF(256, curve[-1].y())
    curve = [S1] + curve + [S2]

    LUTX = [p.x() for p in curve]
    LUTY = [p.y() for p in curve]

    #build LUTXY table
    LUTXY = -np.interp(range(256), LUTX, LUTY)
    LUTXY = np.around(LUTXY).astype(int)
    LUTXY = np.clip(LUTXY, 0, 255)
    return LUTXY

def updateScene(grScene):
    """
    Update all curves in the scene.
    """
    for item in grScene.items():
        item.updatePath()
    #grScene.onUpdateScene()

class myGraphicsPathItem (QGraphicsPathItem):
    """
    Base class for GraphicsPathItems.
    Add method updatePath
    """
    def updatePath(self):
        pass

class activePoint(myGraphicsPathItem):
    def __init__(self, x,y, parentItem=None):
        super(myGraphicsPathItem, self).__init__()
        self.setParentItem(parentItem)
        #self.position_ = QPointF(x,y)
        self.setPos(QPointF(x,y))
        self.moveStart=QPointF()
        self.setPen(QPen(QColor(255, 0, 0), 2))
        qpp = QPainterPath()
        qpp.addEllipse(0,0, 8, 8)
        self.setPath(qpp)


    def mousePressEvent(self, e):
        self.moveStart = e.pos()

    def mouseMoveEvent(self, e):
        self.position_ = e.scenePos()
        self.setPos(e.scenePos())
        updateScene(self.scene())

    def mouseReleaseEvent(self, e):
        self.scene().fixedPoints.sort(key=lambda p : p.scenePos().x())
        self.position_=e.scenePos()
        self.setPos(e.scenePos())
        sc = self.scene()
        if self.moveStart == e.pos():
            self.scene().fixedPoints.remove(self)
            sc.removeItem(self)
            updateScene(sc)
        updateScene(self.scene())
        self.scene().onUpdateScene()
        self.scene().onUpdateLUT()
        sc.onUpdateScene()
        img=self.scene().targetImage
        self.scene().histImg = img.histogram()



class cubicItem(myGraphicsPathItem) :

    def __init__(self, size, parentItem=None):
        super(cubicItem, self).__init__()
        self.setParentItem(parentItem)
        self.qpp = QPainterPath()
        # initial curve : diagonal
        self.qpp.lineTo(QPoint(size, -size))
        # stroke curve
        stroker=QPainterPathStroker()
        stroker.setWidth(strokeWidth)
        self.mboundingPath = stroker.createStroke(self.qpp)
        self.setPath(self.mboundingPath)
        self.clicked=QPoint(0,0)
        self.selected = False

    def updatePath(self):
        qpp = QPainterPath()
        X = np.array([item.x() for item in self.scene().fixedPoints])
        Y = np.array([item.y() for item in self.scene().fixedPoints])

        """
        xValues, yValues = cubicSplineCurve(X, Y)
        for i in range(len(xValues)):
            polygon.append(QPointF(xValues[i], yValues[i]))
        """
        l = cubicSplineCurve(X, Y, clippingInterval= [-self.scene().axeSize, 0])#self.scene().axeSize])
        polygon = QPolygonF(l)
        qpp.addPolygon(polygon)

        # stroke path
        stroker = QPainterPathStroker()
        stroker.setWidth(3)
        # mboundingPath = QPainterPath(qpp)
        mboundingPath = stroker.createStroke(qpp)
        # self.setPath(mboundingPath + qpp1)
        self.setPath(mboundingPath)
        LUT=[]
        LUT.extend([int((-p.y())*255.0/800.0) for p in l])
        self.scene().LUTXY = np.array(LUT) #buildLUT(LUT)

    """

    def updatePathOld(self):
        lfixedPoints = self.scene().fixedPoints

        t = 0.2

        mvptIndex = 1
        qpp = QPainterPath()
        qpp1 = QPainterPath()

        if lfixedPoints[mvptIndex].position().x() < -lfixedPoints[mvptIndex].position().y():
            initila = QPointF(-1, 0) * t * lfixedPoints[mvptIndex].position().y()
        else:
            initila = QPointF(0, -1) * t * lfixedPoints[mvptIndex].position().y()

        if computeControlPoints :
            cp = lfixedPoints[mvptIndex - 1].position() + initila
            self.scene().tangents[0].controlPoint=cp
            self.scene().tangents[0].contactPoint=lfixedPoints[mvptIndex-1].position()
            #print 'tangent0', self.scene().tangents[0].contactPoint, self.scene().tangents[0].controlPoint
        else :
            cp = self.scene().tangents[0].controlPoint

        qpp.moveTo(lfixedPoints[mvptIndex - 1].position())

        LUT=[]
        for i in range(0, len(lfixedPoints) - mvptIndex):
            # draw curve
            qpp.quadTo(cp, lfixedPoints[mvptIndex + i].position())

            #ecart = abs(lfixedPoints[mvptIndex + i].position().x() - lfixedPoints[mvptIndex +i - 1].position().x()) + abs(cp.x())  #take abs and add abs(cp.x())

            lgth = qBezierLen(lfixedPoints[mvptIndex + i - 1].position(), cp, lfixedPoints[mvptIndex + i].position())
            gap = int(self.scene().sampleSize/lgth)
            idx = np.arange(0, len(self.scene().tSample1), max(1, gap), dtype=int)
            #print 'spread', int(sampleSize/lgth)


            LUT.extend(self.scene().tSample1[idx] * lfixedPoints[mvptIndex +i - 1].position() + self.scene().tSample2[idx]* cp + self.scene().tSample3[idx] * lfixedPoints[mvptIndex + i].position())
            # self.qpp.addEllipse(lfixedPoints[mvptIndex + i].position(), 3, 3)
            # draw tangents
            qpp1.moveTo(lfixedPoints[mvptIndex + i-1].position())
            qpp1.lineTo(cp)
            qpp1.moveTo(lfixedPoints[mvptIndex + i].position())
            qpp1.lineTo(cp)
            #qpp1.lineTo(lfixedPoints[mvptIndex + i].pos())
            qpp1.addEllipse(cp, 3, 3)
            #tangents[i].setPath(qpp1)
            qpp.moveTo(lfixedPoints[mvptIndex + i].position())
            #print 'f', mvptIndex, mvptIndex + i, lfixedPoints[mvptIndex + i].pos(), cp, initila
            if computeControlPoints and i < len(lfixedPoints) - mvptIndex - 1:
                cp = 2 * lfixedPoints[mvptIndex + i].position() - cp
                self.scene().tangents[2*(i+1)].controlPoint=cp
                self.scene().tangents[2*(i+1)].contactPoint=lfixedPoints[mvptIndex+i].position()
                self.scene().tangents[2 * (i + 1)+1].controlPoint = cp
                self.scene().tangents[2 * (i + 1)+1].contactPoint = lfixedPoints[mvptIndex + i+1].position()
            else:
                if 2*(i+1)<len(self.scene().tangents):
                    cp = self.scene().tangents[2*(i+1)].controlPoint
        #qpp.moveTo(lfixedPoints[mvptIndex - 1].position())
        #cp = lfixedPoints[mvptIndex - 1].position() - initila

        #stroke path
        stroker = QPainterPathStroker()
        stroker.setWidth(5)
        #mboundingPath = QPainterPath(qpp)
        mboundingPath = stroker.createStroke(qpp);
        # self.setPath(mboundingPath + qpp1)
        self.setPath(mboundingPath)
        self.scene().LUTXY = buildLUT(LUT)
        #print len(LUTX), max([abs(p.x() - q.x()) for p,q in zip(LUT[1:], LUT[:-1])])
    """

    def mousePressEvent(self, e):
        self.beginMouseMove = e.pos()
        self.selected= True

    def mouseMoveEvent(self, e):
        #self.updatePath()
        updateScene(self.scene())


    def mouseReleaseEvent(self, e):
        self.selected = False
        # click event
        if self.beginMouseMove == e.pos():
            #add point
            p=e.pos()
            a=activePoint(p.x(), p.y(), parentItem=self.scene().cubicItem)
            self.scene().fixedPoints.append(a)
            self.scene().fixedPoints.sort(key=lambda z : z.scenePos().x())
            self.scene().addItem(a)
            updateScene(self.scene())
            self.scene().onUpdateScene()
            self.scene().onUpdateLUT()

class graphicsForm(QGraphicsView) :

    @classmethod
    def getNewWindow(cls, cModel, targetImage=None, size=500, layer=None, parent=None):
        newWindow = graphicsForm(size, cModel, targetImage=targetImage, layer=layer, parent=parent)
        newWindow.setWindowTitle(layer.name)
        return newWindow

    def __init__(self, size, cModel, targetImage=None, layer=None, parent=None):
        super(graphicsForm, self).__init__(parent=parent)

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setMinimumSize(size + 80, size + 200)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setBackgroundBrush(QBrush(Qt.black, Qt.SolidPattern))
        self.bgPixmap = QPixmap.fromImage(hueSatModel.colorWheel(size, size, cModel))
        self.graphicsScene = QGraphicsScene()
        self.setScene(self.graphicsScene)
        self.scene().targetImage = targetImage
        self.scene().layer = layer
        self.scene().histImg=None
        #self.LUTXY = LUTXY
        self.graphicsScene.LUTXY=np.array(range(256))

        self.graphicsScene.onUpdateScene = lambda : 0

        self.graphicsScene.axeSize = size


        self.graphicsScene.sampleSize = 400
        self.graphicsScene.tSample = [float(i) / self.graphicsScene.sampleSize for i in range(self.graphicsScene.sampleSize + 1)]
        self.graphicsScene.tSample1 = np.array([(1 - t) ** 2 for t in self.graphicsScene.tSample])
        self.graphicsScene.tSample2 = np.array([2 * t * (1 - t) for t in self.graphicsScene.tSample])
        self.graphicsScene.tSample3 = np.array([t ** 2 for t in self.graphicsScene.tSample])

        # draw axes
        item=myGraphicsPathItem()
        item.setPen(QPen(QBrush(QColor(255, 0, 0)), 1, style=Qt.DashLine))
        qppath = QPainterPath()
        qppath.moveTo(QPoint(0, 0))
        qppath.lineTo(QPoint(self.graphicsScene.axeSize, 0))
        qppath.lineTo(QPoint(self.graphicsScene.axeSize, -self.graphicsScene.axeSize))
        qppath.lineTo(QPoint(0, -self.graphicsScene.axeSize))
        qppath.closeSubpath()
        qppath.lineTo(QPoint(self.graphicsScene.axeSize, -self.graphicsScene.axeSize))

        #add axes
        item.setPath(qppath)
        self.graphicsScene.addItem(item)

        #self.graphicsScene.addPath(qppath, QPen(Qt.DashLine))  #create and add QGraphicsPathItem

        #add curve
        cubic = cubicItem(self.graphicsScene.axeSize)
        self.scene().cubicItem = cubic
        self.graphicsScene.addItem(cubic)

        #add fixed points
        # fixed points
        self.graphicsScene.fixedPoints = [activePoint(0, 0, parentItem=cubic),
                                          activePoint(self.graphicsScene.axeSize / 2, -self.graphicsScene.axeSize / 2, parentItem=cubic),
                                          activePoint(self.graphicsScene.axeSize, -self.graphicsScene.axeSize, parentItem=cubic)]

        for p in self.graphicsScene.fixedPoints :
            self.graphicsScene.addItem(p)


    def drawBackground(self, qp, qrF):
        s = self.graphicsScene.axeSize
        if self.scene().histImg is not None:
            qp.drawPixmap(QRect(0,-s, s, s), QPixmap.fromImage(self.scene().histImg))


