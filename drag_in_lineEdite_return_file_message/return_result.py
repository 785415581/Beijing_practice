#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys
sys.path.append(r'G:\Beijing')
import os
import fllb
from PySide import QtGui,QtCore

class window(QtGui.QWidget):

    def __init__(self,parent = None):

        super(window, self).__init__(parent)
        self.initUI()

    def initUI(self):

        self.edit = LineEdit()
        self.edit.setText(u'请拖入要解析的文件')
        self.edit.setReadOnly(True)
        button = QtGui.QPushButton(u'解析')
        self.text = QtGui.QTextEdit()
        lay = QtGui.QHBoxLayout()
        lay.addWidget(self.edit)
        lay.addWidget(button)

        Vlay = QtGui.QVBoxLayout()
        Vlay.addLayout(lay)
        Vlay.addWidget(self.text)

        self.setLayout(Vlay)
        button.clicked.connect(self.analysisfile)

    # def startfile(self):
    #     path = self.edit.text()
    #     os.startfile(path)

    def analysisfile(self):
        path = self.edit.text()
        result = fllb.query(path)
        for i in range(len(result)):
            self.text.setText(str(result[i])+'\n')
        # self.text.setText(str(result))

class LineEdit(QtGui.QLineEdit):

    def __init__(self,parent = None):
        super(LineEdit, self).__init__(parent)
        self.setDragEnabled(True)

    def dragEnterEvent(self, event):
        event.accept()

    def dragMoveEvent(self,event):
        data = event.mimeData()
        path = data.urls()[0].path()
        realpath = path.split(':')[0].split('/')[-1] +':' + path.split(':')[-1]
        if data.hasUrls():
            self.setEnabled(True)
            self.setText(realpath)
        else:
            self.setText("Cannot display data")

if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)
    window = window()
    window.show()
    app.exec_()



