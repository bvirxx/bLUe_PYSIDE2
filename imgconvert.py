"""
Copyright (C) 2017  Bernard Virot

PeLUT - Photo editing software using adjustment layers with 1D and 3D Look Up Tables.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""

import numpy as np
from PyQt4.QtGui import QImage
from PIL import Image

def ndarrayToQImage(ndimg, format=QImage.Format_ARGB32):
    """
    Convert a 3D numpy ndarray to a QImage. No sanity check is
    done concerning the compatibility between the ndarray shape and
    the QImage format. Although the doc is unclear, it seems that the
    buffer is copied when needed.
    :param ndimg: The ndarray to be converted
    :param format: The QImage format (default ARGB32)
    :return: The converted image
    """

    if ndimg.ndim != 3 or ndimg.dtype != 'uint8':
        raise ValueError("ndarray2QImage : array must be 3D with dtype=uint8, found ndim=%d, dtype=%s" %(ndimg.ndim, ndimg.dtype))

    bytePerLine = ndimg.shape[1] * ndimg.shape[2]
    if len(ndimg.data)!=ndimg.shape[0]*bytePerLine :
        raise ValueError("ndarrayToQImage : conversion error")
    # build QImage from buffer
    qimg = QImage(ndimg.data, ndimg.shape[1], ndimg.shape[0], bytePerLine, format)
    if qimg.format() == QImage.Format_Invalid:
        raise ValueError("ndarrayToQImage : wrong conversion")

    return qimg

def QImageBuffer(qimg):
    """
    Get the QImage buffer as a numpy ndarray with dtype uint8. The size of the
    3rd axis depends on the image type. Pixel color is
    in BGRA order (little endian arch. (intel)) or ARGB (big  endian arch.)
    Format 1 bit per pixel is not supported
    :param qimg: QImage
    :return: The buffer array
    """
    # pixel depth
    bpp = qimg.depth()
    if bpp == 1:
        print "Qimage2array : unsupported image format 1 bit per pixel"
        return None
    Bpp = bpp / 8

    # image buffer (sip.array of Bytes)
    # Calling bits() performs a deep copy of the buffer,
    # suppressing dependencies due to implicit data sharing.
    # To avoid deep copy use constBits() instead.
    ptr = qimg.bits()
    ptr.setsize(qimg.byteCount())

    #convert sip array to ndarray and reshape
    h,w = qimg.height(), qimg.width()
    return np.asarray(ptr).reshape(h, w, Bpp)


def PilImageToQImage(pilimg) :
    """
    Convert a PIL image to a QImage
    :param pilimg: The PIL image, mode RGB
    :return: QImage object format RGB888
    """
    w, h = pilimg.width, pilimg.height
    mode = pilimg.mode

    if mode != 'RGB':
        raise ValueError("PilImageToQImage : wrong mode : %s" % mode)

    # get data buffer (type str)
    data = pilimg.tobytes('raw', mode)

    if len(data) != w * h * 3:
        raise ValueError("PilImageToQImage : incorrect buffer length : %d, should be %d" % (len(data), w * h * 3))

    BytesPerLine = w * 3
    qimFormat = QImage.Format_RGB888

    return QImage(data, w, h, BytesPerLine, qimFormat )


def QImageToPilImage(qimg) :
    """
    Convert a QImage to a PIL image
    :param qimg: The Qimage
    :return: PIL image  object, mode RGB
    """
    a = QImageBuffer(qimg)

    if (qimg.format() == QImage.Format_ARGB32) or (qimg.format() == QImage.Format_RGB32):
        # convert pixels from BGRA or BGRX to RGB
        a=a[:,:,:3][:,:,::-1]
        a = np.ascontiguousarray(a)
    else :
        raise ValueError("QImageToPilImage : unrecognized format : %s" %qimg.Format())

    w, h = qimg.width(), qimg.height()

    return Image.frombytes('RGB', (w,h), a.data)