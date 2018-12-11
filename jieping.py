import sys

try:
    from PySide2 import QtWidgets
    from PySide2 import QtGui
    from PySide2 import QtCore
except ImportError:
    raise ImportError("You need PyQt installed for using this tool.")
    sys.exit()


class Rubb(QtWidgets.QLabel):
    def __init__(self,parent=None, name=None):

        super(Rubb, self).__init__(parent)
        self._parent = parent
        self.name = name
        self.createWidgets()
        # install event filter
        self.fullScreenLabel.installEventFilter(self)

    def eventFilter(self, widget, event):
        if widget != self.fullScreenLabel:
            return QtWidgets.QLabel.eventFilter(self, widget, event)
        if event.type() == QtCore.QEvent.MouseButtonPress:
            if event.button() == QtCore.Qt.RightButton:
                # close full screen win
                self.fullScreenLabel.close()
            if event.button() == QtCore.Qt.LeftButton:
                self.leftMousePress = True
                self.origin = event.pos()
                if not self.rubberBand:
                    self.rubberBand = QtGui.QRubberBand(QtGui.QRubberBand.Rectangle, self.fullScreenLabel)
                self.rubberBand.setGeometry(QtCore.QRect(self.origin, QtCore.QSize()))
                self.rubberBand.show()
                return True
        if event.type() == QtCore.QEvent.MouseMove:

            if self.leftMousePress:
                if self.rubberBand:
                    self.rubberBand.setGeometry(QtCore.QRect(self.origin, event.pos()).normalized())
                return True
        if event.type() == QtCore.QEvent.MouseButtonRelease:
            self.leftMousePress = False
            if self.rubberBand:
                self.termination = event.pos()
                self.rect = QtCore.QRect(self.origin, self.termination)
                self.screenshot = self.fullScreenPixmap.copy(self.rect.x(), self.rect.y(), self.rect.width(),
                                                             self.rect.height())
                # save
                self.screenshot.save(self.name, 'jpg')
                # close
                self.fullScreenLabel.close()
                # picture = QtGui.QImage(self.name)
                # pic_rescaled = picture.scaled(136, 136)
                # pic_rescaled.save(self.name, "jpg")
                self._parent.cameraButton.setIcon(QtGui.QIcon(self.name))
            return True
        return False

    def createWidgets(self):
        self.fullScreenLabel = QtWidgets.QLabel()
        self.fullScreenLabel.setCursor(QtCore.Qt.CrossCursor)

        self.fullScreenLabel.setAutoFillBackground(True)

        self.shotScreenLabel = QtWidgets.QLabel()
        self.rubberBand = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self.fullScreenLabel)
        pal = QtGui.QPalette()
        pal.setBrush(QtGui.QPalette.Highlight, QtGui.QBrush(QtCore.Qt.red))
        self.rubberBand.setPalette(pal)

        self.leftMousePress = False

        self.fullScreenPixmap = QtGui.QPixmap.grabWindow(QtWidgets.QApplication.desktop().winId())
        self.fullScreenLabel.setPixmap(self.fullScreenPixmap)

        self.fullScreenLabel.showFullScreen()