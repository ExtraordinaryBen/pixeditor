#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import Qt

# change widgetsize on frame/layer change
# copy/paste > frame lenght as object
# organize layers

class Viewer(QtGui.QScrollArea):
    """ QScrollArea you can move with midbutton"""
    resysing = QtCore.pyqtSignal(tuple)
    def __init__ (self):
        QtGui.QScrollArea.__init__(self)
        self.setAlignment(QtCore.Qt.AlignLeft)
        
    def event(self, event):
        """ capture middle mouse event to move the view """
        # clic: save position
        if   (event.type() == QtCore.QEvent.MouseButtonPress and
              event.button()==QtCore.Qt.MidButton):
            self.mouseX,  self.mouseY = event.x(), event.y()
            return True

        # drag: move the scrollbars
        elif (event.type() == QtCore.QEvent.MouseMove and
               event.buttons() == QtCore.Qt.MidButton):
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - (event.x() - self.mouseX))
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - (event.y() - self.mouseY))
            self.mouseX,  self.mouseY = event.x(), event.y()
            return True
        elif (event.type() == QtCore.QEvent.Resize):
            self.resysing.emit((event.size().width(), event.size().height()))
            #~ self.widget().adjustSize(event.size().width(), event.size().height())
        return QtGui.QScrollArea.event(self, event)

class LayersCanvas(QtGui.QWidget):
    """ preview of the image and interation with the mouse """
    def __init__(self, parent):
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.setFixedWidth(60)
        
        self.white = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        self.black = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        self.font = QtGui.QFont('SansSerif', 8, QtGui.QFont.Normal)
        self.layerH = 20
        self.margeH = 22
        
    def paintEvent(self, ev=''):
        lH, mH = self.layerH, self.margeH
        p = QtGui.QPainter(self)
        p.setPen(QtGui.QPen(self.black))
        p.setFont(self.font)
        
        # background
        p.fillRect (0, 0, self.width(), mH-2, self.white)
        p.drawLine (0, mH-2, self.width(), mH-2)
        # currentLayer
        p.fillRect(0, (self.parent.project.currentLayer * lH) + mH-1,
                   self.width(), lH, self.white)
        # layer's names
        y = mH
        for i, layer in enumerate(self.parent.project.frames, 1):
            y += lH
            #~ y = (i * lH) + mH
            p.drawText(4, y-6, layer["name"])
            p.drawLine (0, y-1, self.width(), y-1)
        
    def event(self, event):
        if (event.type() == QtCore.QEvent.MouseButtonPress and
                       event.button()==QtCore.Qt.LeftButton):
            item = self.layer_at(event.y())
            if item is not None:
                self.parent.project.currentLayer = item
                self.update()
        return QtGui.QWidget.event(self, event)
    
    def layer_at(self, y):
        l = (y - 23) // 20
        if 0 <= l < len(self.parent.project.frames):
            return l
        return None
            
        
class TimelineCanvas(QtGui.QWidget):
    """ preview of the image and interation with the mouse
    """
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        self.parent = parent
        self.grey = QtGui.QBrush(QtGui.QColor(193, 193, 193))
        self.white = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        self.whitea = QtGui.QBrush(QtGui.QColor(255, 255, 255, 127))
        self.black = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        self.frameWidth = 13
        self.frameHeight = 20
        self.margeX = 1
        self.margeY = 22
        self.strechFrame = False
        self.setMinimumSize(self.getMiniSize()[0], self.getMiniSize()[1])

    def paintEvent(self, ev=''):
        """ draw the widget """
        fW, fH = self.frameWidth, self.frameHeight
        mX, mY = self.margeX, self.margeY
        p = QtGui.QPainter(self)
        fontLight = QtGui.QFont('SansSerif', 7, QtGui.QFont.Light)
        fontBold = QtGui.QFont('SansSerif', 8, QtGui.QFont.Normal)
        p.setPen(QtGui.QPen(self.grey))
        p.setBrush(self.whitea)
        
        # background
        p.fillRect (0, 0, self.width(), 21, self.white)
        p.drawLine (0, 21, self.width(), 21)
        for j, i in enumerate(xrange(7, self.width(), fW), 1):
            p.drawLine (i-7, 19, i-7, 21)
            
            if j % 5 == 0:
                p.setFont(fontLight)
                metrics = p.fontMetrics()
                fw = metrics.width(str(j))
                p.drawText(i-fw/2, 17, str(j))
            
            if j % self.parent.project.fps == 0:
                p.setFont(fontBold)
                metrics = p.fontMetrics()
                s = str(j//self.parent.project.fps)
                fw = metrics.width(s)
                p.drawText(i-fw/2, 10, s)
        
        if self.parent.selection:
            l = self.parent.selection[0]
            f1, f2 = self.parent.selection[1], self.parent.selection[2]
            # remet a l'endroit
            if f2 < f1:
                f1, f2, = f2, f1
            p.fillRect((f1 * fW) + mX, (l * fH) + mY, 
                       (f2 - f1 + 1) * fW, fH, self.white)
            
        # current frame
        p.drawLine(self.parent.project.currentFrame*fW, 0, 
                   self.parent.project.currentFrame*fW, self.height())
        p.drawLine(self.parent.project.currentFrame*fW + fW , 0, 
                   self.parent.project.currentFrame*fW + fW , self.height())
        framesRects = []
        strechRects = []
        self.strechBoxList = []
        for y, layer in enumerate(self.parent.project.frames):
            self.strechBoxList.append([])
            for x, frame in enumerate(layer["frames"]):
                if frame:
                    w, h = 9, 17
                    s = x
                    while 1:
                        s += 1
                        if s < len(layer["frames"]) and not layer["frames"][s]:
                            w += 13
                        else:
                            break
                    nx = x * fW + mX + 1
                    ny = y * fH + mY + 1
                    framesRects.append(QtCore.QRect(nx, ny, w, h))
                    strechrect = QtCore.QRect(nx+w-9, ny+h-9, 9, 9)
                    strechRects.append(strechrect)
                    self.strechBoxList[y].append(strechrect)
                else:
                    self.strechBoxList[y].append(False)
        p.drawRects(framesRects)
        p.setBrush(self.white)
        p.drawRects(strechRects)
        
    def getMiniSize(self):
        """ return the minimum size of the widget 
            to display all frames and layers """
        minH = (len(self.parent.project.frames)*self.frameHeight) + self.margeY
        #get the longest layer
        maxF = max([len(l["frames"]) for l in self.parent.project.frames])
        minW = (maxF * self.frameWidth) + self.margeX
        return (minW, minH)
        
    def event(self, event):
        if   (event.type() == QtCore.QEvent.MouseButtonPress and
              event.button()==QtCore.Qt.LeftButton):
            frame = self.frame_at(event.x())
            layer = self.layer_at(event.y())
            if frame is not None and layer is not None:
                strech = self.is_in_strech_box(event.pos())
                if strech is not None:
                    self.strechFrame = (strech[1], frame)
                    self.parent.selection = False
                else:
                    self.parent.selection = [layer, frame, frame]
                    self.strechFrame = False
            else:
                self.strechFrame = False
                self.parent.selection = False
            self.parent.layersCanvas.update()
            self.update()
            self.parent.change_current(frame, layer)
            return True
        elif (event.type() == QtCore.QEvent.MouseMove and
              event.buttons() == QtCore.Qt.LeftButton):
            frame = self.frame_at(event.x())
            layer = self.layer_at(event.y())
            if frame is not None:
                if self.parent.selection:
                    self.parent.selection[2] = frame
            if     (layer is not None and not self.strechFrame and
                    not self.parent.selection):
                self.parent.project.currentLayer = layer
            self.strech(frame)
            self.parent.layersCanvas.update()
            self.update()
            self.parent.change_current(frame, layer)
            return True
        return QtGui.QWidget.event(self, event)
        
    def is_in_strech_box(self, pos):
        for layer, i in enumerate(self.strechBoxList):
            for frame, j in enumerate(i):
                if j and j.contains(pos):
                    return (frame, layer)
        return None
        
    def strech(self, f):
        if self.strechFrame:
            sl, sf = self.strechFrame[0], self.strechFrame[1]
            while f > sf:
                self.parent.project.frames[sl]["frames"].insert(sf+1, 0)
                sf += 1
            while f < sf:
                if not self.parent.project.frames[sl]["frames"][sf]:
                    self.parent.project.frames[sl]["frames"].pop(sf)
                    sf -= 1
                else:
                    break
            self.update()
            self.strechFrame = (sl, sf)
        
    def frame_at(self, x):
        s = (x - self.margeX)  // self.frameWidth
        if 0 <= s <= self.width() // self.frameWidth:
            return s
        return None
        
    def layer_at(self, y):
        l = ((y - self.margeY) // self.frameHeight)
        if 0 <= l < len(self.parent.project.frames):
            return l
        return None
        
        
########################################################################
class Timeline(QtGui.QWidget):
    """ main windows of the application """
    def __init__(self, project):
        QtGui.QWidget.__init__(self)
        self.project = project
        
        self.frames = [{"frames" : [1, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0], "pos" : 0, "visible" : True, "lock" : False, "name": "Layer 01"},
                       {"frames" : [1, 1, 0, 0, 1, 1, 0, 1, 0, 1], "pos" : 0, "visible" : True, "lock" : False, "name": "Layer 02"},
                       {"frames" : [1, 1, 0, 0, 1, 1, 0, 1, 0, 1], "pos" : 0, "visible" : True, "lock" : False, "name": "Layer 03"}]
        self.currentFrame = 0
        self.currentLayer = 0
        self.selection = False
        self.fps = 12
        self.to_paste = False
        
        ### viewer ###
        self.layersCanvas = LayersCanvas(self)
        self.layersV = Viewer()
        self.layersV.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.layersV.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.layersV.setWidget(self.layersCanvas)
        
        self.timelineCanvas = TimelineCanvas(self)
        self.timelineV = Viewer()
        self.timelineV.setWidget(self.timelineCanvas)
        self.timelineV.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.timelineV.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.timeVSize = (0, 0)
        self.timelineV.resysing.connect(self.adjustSize)
        
        self.layersV.verticalScrollBar().valueChanged.connect(
                lambda v: self.timelineV.verticalScrollBar().setValue(v))
        self.timelineV.verticalScrollBar().valueChanged.connect(
                lambda v: self.layersV.verticalScrollBar().setValue(v))
        
        ### shortcuts ###
        shortcut = QtGui.QShortcut(self)
        shortcut.setKey(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_X))
        shortcut.activated.connect(self.cut)
        shortcopy = QtGui.QShortcut(self)
        shortcopy.setKey(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_C))
        shortcopy.activated.connect(self.copy)
        shortpaste = QtGui.QShortcut(self)
        shortpaste.setKey(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_V))
        shortpaste.activated.connect(self.paste)
        
        ### adding and deleting images ###
        self.addFrameW = QtGui.QToolButton()
        self.addFrameW.setAutoRaise(True)
        self.addFrameW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/frame_add.png")))
        self.addFrameW.clicked.connect(self.add_frame_clicked)
        self.dupFrameW = QtGui.QToolButton()
        self.dupFrameW.setAutoRaise(True)
        self.dupFrameW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/frame_dup.png")))
        self.dupFrameW.clicked.connect(self.duplicate_frame_clicked)
        self.delFrameW = QtGui.QToolButton()
        self.delFrameW.setAutoRaise(True)
        self.delFrameW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/frame_del.png")))
        self.delFrameW.clicked.connect(self.delete_frame_clicked)
        self.clearFrameW = QtGui.QToolButton()
        self.clearFrameW.setAutoRaise(True)
        self.clearFrameW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/frame_clear.png")))
        self.clearFrameW.clicked.connect(self.clear_frame_clicked)

        ### adding and deleting layers ###
        self.addLayerW = QtGui.QToolButton()
        self.addLayerW.setAutoRaise(True)
        self.addLayerW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/layer_add.png")))
        self.addLayerW.clicked.connect(self.add_layer_clicked)
        self.dupLayerW = QtGui.QToolButton()
        self.dupLayerW.setAutoRaise(True)
        self.dupLayerW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/layer_dup.png")))
        self.dupLayerW.clicked.connect(self.duplicate_layer_clicked)
        self.delLayerW = QtGui.QToolButton()
        self.delLayerW.setAutoRaise(True)
        self.delLayerW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/layer_del.png")))
        self.delLayerW.clicked.connect(self.delete_layer_clicked)
        
        ### play the animation ###
        self.playFrameW = QtGui.QToolButton()
        self.playFrameW.state = "play"
        self.playFrameW.setAutoRaise(True)
        self.playFrameW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/play_play.png")))
        self.playFrameW.clicked.connect(self.play_pause_clicked)
        self.framerate = 1/12
        self.framerateL = QtGui.QLabel("fps")
        self.framerateW = QtGui.QLineEdit(self)
        self.framerateW.setText(str(12))
        self.framerateW.setValidator(QtGui.QIntValidator(self.framerateW))
        self.framerateW.textChanged.connect(self.framerate_changed)

        self.repeatW = QtGui.QToolButton()
        self.repeatW.state = False
        self.repeatW.setAutoRaise(True)
        self.repeatW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/play_no_repeat.png")))
        self.repeatW.clicked.connect(self.repeat_clicked)

        ### layout ###
        toolbox = QtGui.QHBoxLayout()
        toolbox.addWidget(self.addFrameW)
        toolbox.addWidget(self.dupFrameW)
        toolbox.addWidget(self.delFrameW)
        toolbox.addWidget(self.clearFrameW)
        toolbox.addStretch(0)
        toolbox.addWidget(self.framerateW)
        toolbox.addWidget(self.framerateL)
        toolbox.addWidget(self.repeatW)
        toolbox.addWidget(self.playFrameW)
        
        toolbox2 = QtGui.QVBoxLayout()
        toolbox2.addWidget(self.addLayerW)
        toolbox2.addWidget(self.dupLayerW)
        toolbox2.addWidget(self.delLayerW)
        toolbox2.addStretch(0)
        
        timeLayout = QtGui.QHBoxLayout()
        timeLayout.addWidget(self.layersV)
        timeLayout.addWidget(self.timelineV)
        
        layout = QtGui.QVBoxLayout()
        layout.addLayout(timeLayout)
        layout.addLayout(toolbox)
        
        layout2 = QtGui.QHBoxLayout()
        layout2.addLayout(toolbox2)
        layout2.addLayout(layout)

        self.setLayout(layout2)

    def change_current(self, frame=None, layer=None):
        if frame is not None:
            self.project.currentFrame = frame
        if layer is not None:
            self.project.currentLayer = layer
        if frame is not None or layer is not None:
            self.project.currentFrameChanged.emit()
    ######## Size adjust ###############################################
    def showEvent(self, event):
        self.timelineCanvas.setMinimumHeight(len(self.project.frames)*20 + 25)
        self.timelineCanvas.update()
        self.layersCanvas.setMinimumHeight(self.timelineCanvas.height())
        self.layersCanvas.update()
        self.layersV.setViewportMargins(0, 0, 0, 
                    self.timelineV.horizontalScrollBar().height())
        self.layersV.setMinimumWidth(self.layersCanvas.width() + 
                    self.layersV.verticalScrollBar().width() + 2)
        self.layersV.setMaximumWidth(self.layersCanvas.width() + 
                    self.layersV.verticalScrollBar().width() + 2)
        
    def adjustSize(self, timeVSize=False):
        if timeVSize:
            self.timeVSize = timeVSize
        else:
            timeVSize = self.timeVSize
        wW = timeVSize[0]
        wH = timeVSize[1] - self.timelineV.horizontalScrollBar().height()
        print timeVSize
        print self.timelineV.viewport().size()
        timeMin = self.timelineCanvas.getMiniSize()
        self.timelineCanvas.setFixedWidth(timeMin[0] + wW - self.timelineCanvas.frameWidth)
        if timeMin[1] > wH-2:
            self.timelineCanvas.setFixedHeight(timeMin[1])
            self.layersCanvas.setFixedHeight(timeMin[1])
        else:
            self.timelineCanvas.setFixedHeight(wH-2)
            self.layersCanvas.setFixedHeight(wH-2)
    
    ######## Copy ######################################################
    def cut(self):
        print "cut"
        if self.selection:
            l = self.selection[0]
            f1, f2 = self.selection[1], self.selection[2]
            if f2 < f1:
                f1, f2, = f2, f1
            prev = f1
            if self.is_in_false(self.project.frames[l]["frames"], prev):
                while not self.project.frames[l]["frames"][prev]:
                    prev -= 1
                else:
                    print prev
                    self.project.frames[l]["frames"][f1] = self.project.frames[l]["frames"][prev]
            nex = f2+1
            if self.is_in_false(self.project.frames[l]["frames"], nex):
                while not self.project.frames[l]["frames"][nex]:
                    nex -= 1
                else:
                    print nex
                    self.project.frames[l]["frames"][f2+1] = self.project.frames[l]["frames"][nex]
                
                
            self.to_paste = self.project.frames[l]["frames"][f1:f2+1]
            del self.project.frames[l]["frames"][f1:f2+1]
            self.timelineCanvas.update()
            
    def copy(self):
        print "copy"
        if self.selection:
            l = self.selection[0]
            f1, f2 = self.selection[1], self.selection[2]
            if f2 < f1:
                f1, f2, = f2, f1
            prev = f1
            if self.is_in_false(self.project.frames[l]["frames"], prev):
                while not self.project.frames[l]["frames"][prev]:
                    prev -= 1
                else:
                    print prev
                    self.project.frames[l]["frames"].insert(f1, self.project.frames[l]["frames"][prev])
                
            self.to_paste = self.project.frames[l]["frames"][f1:f2+1]
        
    def paste(self):
        print "paste"
        if self.to_paste:
            f = self.currentFrame
            l = self.currentLayer
            while f > len(self.project.frames[l]["frames"]):
                self.project.frames[l]["frames"].append(0)
            for n, i in enumerate(self.to_paste):
                print n
                self.project.frames[l]["frames"].insert(f+n, i)
            self.timelineCanvas.update()
            
    def is_in_false(self, li, i):
        if 0 <= i < len(li) and not li[i]:
            return True
        return False
            
    ######## Buttons ###################################################
    def add_frame_clicked(self):
        #~ self.project.frames[0]["frames"].append(self.project.make_canvas())
        self.project.frames[0]["frames"].insert(self.project.currentFrame, self.project.make_canvas())
        self.timelineCanvas.update()
        
    def delete_frame_clicked(self):
        self.project.frames[0]["frames"].pop(self.project.currentFrame)
        self.timelineCanvas.update()
        
    def duplicate_frame_clicked(self):
        pass
        
    def clear_frame_clicked(self):
        pass
        
    def add_layer_clicked(self):
        pass
        
    def duplicate_layer_clicked(self):
        pass
        
    def delete_layer_clicked(self):
        pass
        
    def play_pause_clicked(self):
        pass
        
    def framerate_changed(self):
        pass
        
    def repeat_clicked(self):
        pass
        
        
