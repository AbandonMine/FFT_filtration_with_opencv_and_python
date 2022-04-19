import sys, cv2, os
import numpy as np
from PySide6 import QtCore, QtWidgets, QtGui

class MouseTracker(QtCore.QObject):
    mouseWasPressedByUser  = QtCore.Signal(QtCore.QPoint)
    mouseWasReleasedByUser = QtCore.Signal(QtCore.QPoint)
    mousePositionChanged   = QtCore.Signal(QtCore.QPoint)

    def __init__(self, widget):
        super().__init__(widget)
        self._widget = widget
        self.widget.setMouseTracking(True)
        self.widget.installEventFilter(self)
        self.isEnabled = False

    def eventFilter(self, o, e):
        if (o is self.widget) & (e.type() == QtCore.QEvent.MouseButtonPress) & self.isEnabled:
            self.mouseWasPressedByUser.emit(e.pos())
        if (o is self.widget) & (e.type() == QtCore.QEvent.MouseButtonRelease) & self.isEnabled:
            self.mouseWasReleasedByUser.emit(e.pos())
        if (o is self.widget) & (e.type() == QtCore.QEvent.MouseMove) & self.isEnabled:
            self.mousePositionChanged.emit(e.pos())
        return super().eventFilter(o, e)

    def setEnabledStatus(self, newValue):
        self.isEnabled = newValue

    @property
    def widget(self):
        return self._widget

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dynamic filter with DFT")

        self.dispImgWidth = 375
        self.dispImgHeight = 225
        defaultPixMap = QtGui.QPixmap(self.dispImgWidth, self.dispImgHeight)
        defaultPixMap.fill(QtGui.QColor('black'))

        self.orgImgLabel             = QtWidgets.QLabel("Original image (converted to gray scale):")
        self.orgImg                  = QtWidgets.QLabel(self)
        self.dftTransformViewLabel   = QtWidgets.QLabel("Transformation result with applied mask (magnitude):")
        self.dftTransformView        = QtWidgets.QLabel(self)
        self.imgAfterFiltrationLabel = QtWidgets.QLabel("Image after filtration:")
        self.imgAfterFiltration      = QtWidgets.QLabel(self)

        self.mouseTracker = MouseTracker(self.dftTransformView)
        self.mouseTracker.mouseWasPressedByUser.connect(self.onMouseWasPressedHandler)
        self.mouseTracker.mouseWasReleasedByUser.connect(self.onMouseWasReleasedHandler)
        self.mouseTracker.mousePositionChanged.connect(self.onMousePositionChangedHandler)
        self.isMousePressed = False

        self.loadImgButton = QtWidgets.QPushButton("Load image")
        self.maskType = ["None", "Circle - Inside", "Circle - Outside", "Rectangle - Inside", "Rectangle - Outside", "Custom"]
        self.maskTypeComboBox = QtWidgets.QComboBox(self)
        self.maskTypeComboBox.addItems(self.maskType)
        self.maskTypeComboBox.setEnabled(False)
        self.filterSizeSliderLabel = QtWidgets.QLabel("Size of the mask:")
        self.filterSizeSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.filterSizeSlider.setMaximum(100)
        self.filterSizeSlider.setMinimum(0)
        self.filterSizeSlider.setTickInterval(1)
        self.filterSizeSlider.setEnabled(False)
        self.incSliderButton = QtWidgets.QPushButton("Increment the slider")
        self.incSliderButton.setEnabled(False)
        self.decSliderButton = QtWidgets.QPushButton("Decrement the slider")
        self.decSliderButton.setEnabled(False)

        self.paintBrushSliderLabel = QtWidgets.QLabel("Size of the custom brush:")
        self.paintBrushSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.paintBrushSlider.setMaximum(100)
        self.paintBrushSlider.setMinimum(1)
        self.brushSize = 5
        self.paintBrushSlider.setTickInterval(1)
        self.paintBrushSlider.setEnabled(False)
        self.clearCustomMaskButton = QtWidgets.QPushButton("Clear custom mask")
        self.clearCustomMaskButton.setEnabled(False)

        self.saveImgToFileButton = QtWidgets.QPushButton("Save image to file")
        self.saveImgToFileButton.setEnabled(False)


        spacerHeight = (self.orgImgLabel.sizeHint().height() + self.dftTransformViewLabel.sizeHint().height() 
                        + self.imgAfterFiltration.sizeHint().height() + self.dispImgHeight*3 - self.loadImgButton.sizeHint().height() 
                        - self.maskTypeComboBox.sizeHint().height() - self.filterSizeSliderLabel.sizeHint().height() 
                        - self.filterSizeSlider.sizeHint().height() - self.incSliderButton.sizeHint().height()
                        - self.decSliderButton.sizeHint().height()  - self.paintBrushSliderLabel.sizeHint().height()
                        - self.paintBrushSlider.sizeHint().height() - self.clearCustomMaskButton.sizeHint().height()
                        - self.saveImgToFileButton.sizeHint().height())
        self.spacer = QtWidgets.QSpacerItem(150, spacerHeight, QtWidgets.QSizePolicy.Expanding)

        vertcalBox = QtWidgets.QVBoxLayout()
        vertcalBox.addWidget(self.orgImgLabel)
        vertcalBox.addWidget(self.orgImg)
        vertcalBox.addWidget(self.dftTransformViewLabel)
        vertcalBox.addWidget(self.dftTransformView)
        vertcalBox.addWidget(self.imgAfterFiltrationLabel)
        vertcalBox.addWidget(self.imgAfterFiltration)

        vertcalBox2 = QtWidgets.QVBoxLayout()
        vertcalBox2.addWidget(self.loadImgButton)
        vertcalBox2.addWidget(self.maskTypeComboBox)
        vertcalBox2.addWidget(self.filterSizeSliderLabel)
        vertcalBox2.addWidget(self.filterSizeSlider)
        vertcalBox2.addWidget(self.incSliderButton)
        vertcalBox2.addWidget(self.decSliderButton)
        vertcalBox2.addWidget(self.paintBrushSliderLabel)
        vertcalBox2.addWidget(self.paintBrushSlider)
        vertcalBox2.addWidget(self.clearCustomMaskButton)
        vertcalBox2.addWidget(self.saveImgToFileButton)
        vertcalBox2.addSpacerItem(self.spacer)

        horizontalBox = QtWidgets.QHBoxLayout()
        horizontalBox.addLayout(vertcalBox)
        horizontalBox.addLayout(vertcalBox2)

        self.setLayout(horizontalBox)

        self.orgImg.setPixmap(defaultPixMap)
        self.dftTransformView.setPixmap(defaultPixMap)
        self.imgAfterFiltration.setPixmap(defaultPixMap)

        self.loadImgButton.clicked.connect(self.loadFile)
        self.maskTypeComboBox.currentTextChanged.connect(self.handleFilterChange)
        self.filterSizeSlider.valueChanged.connect(self.handleSliderChange) 
        self.incSliderButton.clicked.connect(self.incButtonClickedHandler)
        self.decSliderButton.clicked.connect(self.decButtonClickedHandler)
        self.paintBrushSlider.valueChanged.connect(self.sizeBrushSLiderHandler)
        self.clearCustomMaskButton.clicked.connect(self.clearCustomMaskedButtonClicked)
        self.saveImgToFileButton.clicked.connect(self.saveFile)

    @QtCore.Slot()
    def loadFile(self):
        fileName = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file with photo', 
                                               (os.path.expanduser('~')+'\Desktop'),"Image files (*.jpg *.png)")
        self.img = cv2.imread(fileName[0])
        if self.img is None:
            return
        self.imgGray = cv2.cvtColor(self.img.astype('uint8'), cv2.COLOR_RGB2GRAY)
        self.setAsGreyPixmap(self.imgGray, self.orgImg)
        self.performFft()
        self.performMaskingAndDisplayResult("None")
        self.performIfftAndDisplayResult()
        self.maskTypeComboBox.setEnabled(True)
        self.saveImgToFileButton.setEnabled(True)

    @QtCore.Slot()
    def saveFile(self):
        normalized_picture = cv2.normalize(self.filtredImg, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
        fileName = QtWidgets.QFileDialog.getSaveFileName(self, 'Pick destination for your saved img', 
                                               (os.path.expanduser('~')+'\Desktop'),"Image files (*.jpg *.png)")
        cv2.imwrite(fileName[0], normalized_picture)

    @QtCore.Slot()
    def handleFilterChange(self, text):
        if (text == "None") | (text == "Custom"):
            self.filterSizeSlider.setEnabled(False)
            self.incSliderButton.setEnabled(False)
            self.decSliderButton.setEnabled(False)
            if(text == "Custom"):
                self.mouseTracker.setEnabledStatus(True)
                self.paintBrushSlider.setEnabled(True)
                self.paintBrushSlider.setSliderPosition(5)
                self.brushSize = 5
                self.clearCustomMaskButton.setEnabled(True)
                self.customMask = np.ones((self.magImg.shape[0], self.magImg.shape[1], 1), np.uint8)
            else:
                self.mouseTracker.setEnabledStatus(False)
                self.paintBrushSlider.setEnabled(False)
                self.clearCustomMaskButton.setEnabled(False)
        else:
            self.filterSizeSlider.setEnabled(True)
            self.incSliderButton.setEnabled(True)
            self.decSliderButton.setEnabled(True)
            self.filterSizeSlider.setSliderPosition(50)
            self.mouseTracker.setEnabledStatus(False)
            self.paintBrushSlider.setEnabled(False)
            self.clearCustomMaskButton.setEnabled(False)
        self.performMaskingAndDisplayResult(text)
        self.performIfftAndDisplayResult()
        
    @QtCore.Slot()
    def handleSliderChange(self, value):
        self.performMaskingAndDisplayResult(self.maskTypeComboBox.currentText())
        self.performIfftAndDisplayResult()

    @QtCore.Slot()
    def incButtonClickedHandler(self):
        newValue = self.filterSizeSlider.sliderPosition() + 1
        if newValue > 100:
            newValue = 100
        self.filterSizeSlider.setSliderPosition(newValue)
    
    @QtCore.Slot()
    def decButtonClickedHandler(self):
        newValue = self.filterSizeSlider.sliderPosition() - 1
        if newValue < 0:
            newValue = 0
        self.filterSizeSlider.setSliderPosition(newValue)

    @QtCore.Slot()
    def sizeBrushSLiderHandler(self, value):
        self.brushSize = value

    @QtCore.Slot()
    def clearCustomMaskedButtonClicked(self):
        self.customMask = np.ones((self.magImg.shape[0], self.magImg.shape[1], 1), np.uint8)
        self.performMaskingAndDisplayResult("Custom")
        self.performIfftAndDisplayResult()

    @QtCore.Slot()
    def onMouseWasPressedHandler(self, pos):
        self.isMousePressed = True
        self.addPointToTheMask(pos)

    @QtCore.Slot()
    def onMouseWasReleasedHandler(self, pos):
        self.isMousePressed = False
        self.addPointToTheMask(pos)
        self.performIfftAndDisplayResult()

    @QtCore.Slot()
    def onMousePositionChangedHandler(self, pos):
        if self.isMousePressed == True:
            self.addPointToTheMask(pos)


    def setAsGreyPixmap(self, what, where):
        height, width = what.shape
        channel = 1
        bytesPerLine = channel * width
        what = cv2.normalize(what, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
        what = what.astype(np.uint8)
        convertedToQTFormat = QtGui.QImage(what, width, height, bytesPerLine , QtGui.QImage.Format_Grayscale8)
        rescaledQImage = convertedToQTFormat.scaled(self.dispImgWidth, self.dispImgHeight, QtCore.Qt.KeepAspectRatio)
        finalQPixmap = QtGui.QPixmap.fromImage(rescaledQImage)
        where.setPixmap(finalQPixmap)

    def performFft(self):
        self.dftImg = cv2.dft(np.float32(self.imgGray),flags = cv2.DFT_COMPLEX_OUTPUT)
        self.dftImgShift = np.fft.fftshift(self.dftImg)
        self.magImg = 20*np.log(cv2.magnitude(self.dftImgShift[:,:,0],self.dftImgShift[:,:,1]))

    def performMaskingAndDisplayResult(self, typeOfMasking):
        if typeOfMasking == "None":
            self.masked = self.magImg
            self.maskedDFT = self.dftImgShift
        elif typeOfMasking == "Circle - Inside":
            mask = np.ones((self.magImg.shape[0], self.magImg.shape[1], 1), np.uint8)
            smallerDimmension = min(self.magImg.shape)
            radiusOfFilterCircle = int(smallerDimmension*(self.filterSizeSlider.sliderPosition()/100))
            mask = cv2.circle(mask, (int(mask.shape[1]/2), int(mask.shape[0]/2)), radiusOfFilterCircle, 0, -1)
            self.masked = cv2.bitwise_and(self.magImg, self.magImg, mask = mask)
            self.masked = self.masked.squeeze()
            self.maskedDFT = self.dftImgShift * mask
        elif typeOfMasking == "Circle - Outside":
            mask = np.zeros((self.magImg.shape[0], self.magImg.shape[1], 1), np.uint8)
            smallerDimmension = min(self.magImg.shape)
            radiusOfFilterCircle = int(smallerDimmension*(self.filterSizeSlider.sliderPosition()/100))
            mask = cv2.circle(mask, (int(mask.shape[1]/2), int(mask.shape[0]/2)), radiusOfFilterCircle, 255, -1)
            self.masked = cv2.bitwise_and(self.magImg, self.magImg, mask = mask)
            self.masked = self.masked.squeeze()
            self.maskedDFT = self.dftImgShift * mask
        elif typeOfMasking == "Rectangle - Inside":
            mask = np.ones((self.magImg.shape[0], self.magImg.shape[1], 1), np.uint8)
            startingPoint = (int(self.magImg.shape[1]/2*(1-self.filterSizeSlider.sliderPosition()/100)),
                             int(self.magImg.shape[0]/2*(1-self.filterSizeSlider.sliderPosition()/100)))
            endingPoint   = (int(self.magImg.shape[1]/2*(1+self.filterSizeSlider.sliderPosition()/100)),
                             int(self.magImg.shape[0]/2*(1+self.filterSizeSlider.sliderPosition()/100)))
            mask = cv2.rectangle(mask, startingPoint, endingPoint, 0, -1)
            self.masked = cv2.bitwise_and(self.magImg, self.magImg, mask = mask)
            self.masked = self.masked.squeeze()
            self.maskedDFT = self.dftImgShift * mask
        elif typeOfMasking == "Rectangle - Outside":
            mask = np.zeros((self.magImg.shape[0], self.magImg.shape[1], 1), np.uint8)
            startingPoint = (int(self.magImg.shape[1]/2*(1-self.filterSizeSlider.sliderPosition()/100)),
                             int(self.magImg.shape[0]/2*(1-self.filterSizeSlider.sliderPosition()/100)))
            endingPoint   = (int(self.magImg.shape[1]/2*(1+self.filterSizeSlider.sliderPosition()/100)),
                             int(self.magImg.shape[0]/2*(1+self.filterSizeSlider.sliderPosition()/100)))
            mask = cv2.rectangle(mask, startingPoint, endingPoint, 255, -1)
            self.masked = cv2.bitwise_and(self.magImg, self.magImg, mask = mask)
            self.masked = self.masked.squeeze()
            self.maskedDFT = self.dftImgShift * mask
        else:
            self.masked = cv2.bitwise_and(self.magImg, self.magImg, mask = self.customMask)
            self.maskedDFT = self.dftImgShift*self.customMask

        self.setAsGreyPixmap(self.masked, self.dftTransformView)

    def performIfftAndDisplayResult(self):
        self.ishifted = np.fft.ifftshift(self.maskedDFT)
        self.filtredImg = cv2.idft(self.ishifted, flags= cv2.DFT_REAL_OUTPUT)
        self.setAsGreyPixmap(self.filtredImg, self.imgAfterFiltration)

    def addPointToTheMask(self, point):
        x_pos = point.x()
        if x_pos > self.dispImgWidth/2:
            x_pos = self.dispImgWidth - x_pos
        x_pos = int(x_pos/self.dispImgWidth*self.magImg.shape[1])

        y_pos = point.y()
        if y_pos > self.dispImgHeight/2:
            y_pos =  self.dispImgHeight - y_pos
        y_pos = int(y_pos/self.dispImgHeight*self.magImg.shape[0])
        
        self.customMask = cv2.circle(self.customMask, (x_pos, y_pos), self.brushSize, 0, -1)
        self.customMask = cv2.circle(self.customMask, (self.magImg.shape[1] - x_pos, y_pos), self.brushSize, 0, -1)
        self.customMask = cv2.circle(self.customMask, (x_pos, self.magImg.shape[0] - y_pos), self.brushSize, 0, -1)
        self.customMask = cv2.circle(self.customMask, (self.magImg.shape[1] - x_pos, self.magImg.shape[0] - y_pos), self.brushSize, 0, -1)

        self.performMaskingAndDisplayResult("Custom")


        

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())