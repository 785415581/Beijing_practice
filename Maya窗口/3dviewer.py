#-*- coding:utf-8 -*-
import maya.OpenMayaUI as omui

import maya.cmds as cmds
import shiboken2
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2 import QtWidgets

#nodeName = cmds.modelPanel(cam="persp")
#print nodeName
def getMainWindow():
    ptr = omui.MQtUtil.mainWindow()
    mainWin = shiboken2.wrapInstance(long(ptr), QMainWindow)
    return mainWin
    
def GetQtWidget(mayaName):
    ptr = omui.MQtUtil.findControl(mayaName)
    if ptr is None:
        ptr = mui.MQtUtil.findLayout(mayaName)
    if ptr is None:
        ptr = mui.MQtUtil.findMenuItem(mayaName)
    if ptr is not None:
        return shiboken2.wrapInstance(long(ptr), QtWidgets.QWidget)
        
class MyLabel(QtWidgets.QLabel):
    def __init__(self,text):
        super(MyLabel,self).__init__()
        self.setText(text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.prePos = event.pos()
    def mouseReleaseEvent(self, event):
        self.prePos = None
    def mouseMoveEvent(self, event):
        if not self.prePos:
            return
        pos = event.pos() - self.prePos
        self.move(self.x() + pos.x(), self.y() + pos.y())

    def mouseDoubleClickEvent(self, event):
        sex, ok = QtWidgets.QInputDialog.getText(self,"rename",u"请输入newname:",QtWidgets.QLineEdit.Normal, " ")
        if ok:
            self.setText(sex)
            #pos = event.pos()
            #self.move(pos.x(),  pos.y())
            #print self.pos()

class MyDialog(QtWidgets.QDialog):
 
    def __init__(self, parent, **kwargs):
        super(MyDialog, self).__init__(parent, **kwargs)
 
        self.setObjectName("MyWindow")
        self.resize(800, 600)
        self.setWindowTitle("PySide")
        self.initUI()
    def initUI(self):
        #self._cameraName = cmds.camera()[0]
        nodeName = cmds.modelPanel(cam="persp")
        self.modelPanel = GetQtWidget(nodeName)
        print self.modelPanel
        self.verticalLayout = QtWidgets.QVBoxLayout()
        #self.verticalLayout.setObjectName("mainLayout")
        self.verticalLayout.addWidget(self.modelPanel)
        
        self.lay=QtWidgets.QHBoxLayout()
        self.MyLabel=MyLabel(u'我的世界')
        self.MyLabel.setStyleSheet("background-color:gray")
        self.MyLabel1=MyLabel(u'我的世界')
        self.MyLabel1.setStyleSheet("background-color:gray")
        self.MyLabel2=MyLabel(u'我的世界')
        self.MyLabel2.setStyleSheet("background-color:gray")
        self.lay.addWidget(self.MyLabel)
        self.lay.addWidget(self.MyLabel1)
        self.lay.addWidget(self.MyLabel2)
        
        
        self.ver=QtWidgets.QVBoxLayout()
        self.ver.addLayout(self.verticalLayout)
        self.ver.addLayout(self.lay)
        self.setLayout(self.ver)
        #self.modelPanel.setLayout(self.lay)
        #self.modelPanel.setlayout(self.lay)
        
    def show(self):
        super(MyDialog, self).show()
        #self.modelPanel.repaint()

def show():

    d = MyDialog( getMainWindow())
    d.show()

 
show()
