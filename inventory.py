#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2016 Juan Vanyo Cerda <juavacer@inf.upv.es>             *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************
import FreeCAD as App
import FreeCADGui as Gui

from GDT import *

class InventoryCommand:
    def __init__(self):
        self.iconPath = ':/dd/icons/inventory.svg'
        self.toolTip = 'Inventory of the elements of GD&T'

    def Activated(self):
        Gui.Control.showDialog( GDTGuiClass() )

    def GetResources(self):
        return {
            'Pixmap' : self.iconPath,
            'MenuText': self.toolTip,
            'ToolTip':  self.toolTip
            }

    def IsActive(self):
        if FreeCADGui.ActiveDocument:
            return True
        else:
            return False

class GDTGuiClass:
    def __init__(self):
        self.widgetsGDT = []
        inventory = getAllAnnotationPlaneObjects() + getAllDatumSystemObjects() + getAllDatumFeatureObjects() + getAllGeometricToleranceObjects()
        
        for obj in inventory:
            self.widget = QtGui.QWidget()
            self.widget.setWindowTitle( obj.Label )
            self.widget.setWindowIcon( obj.ViewObject.Icon )
            self.widgetsGDT.append(self.widget)
            self.dialogWidgets = []
            vbox = QtGui.QVBoxLayout()
            hbox = QtGui.QHBoxLayout()
            self.data = ContainerOfData()
            self.data.textName = obj.Label
            
            if "AnnotationPlane" == getType(obj):
                self.dialogWidgets.append(textLabelWidget_inv(Text = 'Name:', Mask = 'NNNn', Data = self.data, Obj = obj))
                self.dialogWidgets.append(fieldLabelButtonWidget_inv(Text = 'Offset:', Data = self.data, Obj = obj))

            elif "DatumSystem" == getType(obj):
                self.dialogWidgets.append(textLabelWidget_inv(Text = 'Name:', Mask='NNNn', Data = self.data, Obj = obj))
                listDF = [None] + [l for l in getAllDatumFeatureObjects()]
                self.dialogWidgets.append( groupBoxWidget_inv(Text='Constituents', List=[comboLabelWidget_inv(Text='Primary:',List=listDF, Data = self.data, Obj = obj),comboLabelWidget_inv(Text='Secondary:',List=listDF, Data = self.data, Obj = obj), comboLabelWidget_inv(Text='Tertiary:',List=listDF, Data = self.data, Obj = obj)], Data = self.data, Obj = obj) )

            elif "DatumFeature" == getType(obj):
                self.dialogWidgets.append(textLabelWidget_inv(Text = 'Datum feature:', Mask='>A', Data = self.data, Obj = obj))
                self.dialogWidgets.append( comboLabelWidget_inv(Text='In annotation:', List = [l for l in getAllAnnotationObjects()], Data = self.data, Obj = obj) )

            elif "GeometricTolerance" == getType(obj):
                self.dialogWidgets.append(textLabelWidget_inv(Text = 'Name:', Mask='NNNn', Data = self.data, Obj = obj))
                characteristics = makeCharacteristics()
                self.dialogWidgets.append( comboLabelWidget_inv(Text='Characteristic:', List=characteristics.Label, Icons=characteristics.Icon, Data = self.data, Obj = obj) )
                
                featureControlFrame = makeFeatureControlFrame()
                
                # Annotation = makeAnnotation(self.data.faces,self.data.AP)
                print("self.data          {}".format(self.data))
                print("self.data textName {}".format(self.data.textName))
                # print("self.data characteristic {}".format(self.data.characteristic))
                print("self.data circumference {}".format(self.data.circumference))


                self.dialogWidgets.append( fieldLabelComboWidget_inv(Text='Tolerance value:', List=featureControlFrame.Label, Circumference=['',':/dd/icons/diameter.svg'] , Icons=featureControlFrame.Icon, ToolTip=featureControlFrame.toolTip, Data = self.data, Obj = obj) ) #http://doc.qt.io/qt-5/qlineedit.html#inputMask-prop
                
                self.dialogWidgets.append( comboLabelWidget_inv(Text='Datum system:', List=[None] + [l for l in getAllDatumSystemObjects()], Data = self.data, Obj = obj) )
                self.dialogWidgets.append( comboLabelWidget_inv(Text='In annotation:', List=[l for l in getAllAnnotationObjects()], Data = self.data, Obj = obj) )


            for widg in self.dialogWidgets:
                w = widg.generateWidget()
                if isinstance(w, QtGui.QLayout):
                    vbox.addLayout( w )
                else:
                    vbox.addWidget( w )

            buttonModify = QtGui.QPushButton('Modify')
            buttonModify.clicked.connect(lambda obj = obj, data = self.data: self.modifyFunc(obj, data))
            buttonDelete = QtGui.QPushButton('Delete')
            buttonDelete.clicked.connect(lambda obj = obj, data = self.data: self.deleteFunc(obj, data))
            
            hbox.addStretch(1)
            hbox.addWidget( buttonModify )
            hbox.addWidget( buttonDelete )
            hbox.addStretch(1)
            vbox.addLayout(hbox)
            self.widget.setLayout(vbox)

        self.form = self.widgetsGDT
    
    """
        Modify Function 
    """
    def modifyFunc(self, obj, data):
        Code = ['', '\u24BB', '\u24C1', '\u24C2', '\u24C5', '\u24C8', '\u24C9', '\u24CA']
        ToolTip = ['Feature control frame', 'Free state', 'Least material condition', 'Maximum material condition', 'Projected tolerance zone', 'Regardless of feature size', 'Tangent plane', 'Unequal Bilateral']
        Icon = ['', ':/dd/icons/FeatureControlFrame/freeState.svg', ':/dd/icons/FeatureControlFrame/leastMaterialCondition.svg', ':/dd/icons/FeatureControlFrame/maximumMaterialCondition.svg', ':/dd/icons/FeatureControlFrame/projectedToleranceZone.svg', ':/dd/icons/FeatureControlFrame/regardlessOfFeatureSize.svg', ':/dd/icons/FeatureControlFrame/tangentPlane.svg', ':/dd/icons/FeatureControlFrame/unequalBilateral.svg']

        
        if "AnnotationPlane" == getType(obj):
            obj.Label = data.textName
            obj.Offset = data.OffsetValue

        elif "DatumSystem" == getType(obj):
            obj.Primary = data.primary
            obj.Secondary = data.secondary
            obj.Tertiary = data.tertiary
            textName = data.textName.split(":")[0]
            if data.primary != None:
                textName+=': '+obj.Primary.Label
                if data.secondary != None:
                    textName+=' | '+obj.Secondary.Label
                    if data.tertiary != None:
                        textName+=' | '+obj.Tertiary.Label
            obj.Label = textName

        elif "DatumFeature" == getType(obj):
            annotationObj = getAnnotationWithDF(obj)
            remove = False
            
            if data.annotation.DF != None and annotationObj != data.annotation:
                QtGui.QMessageBox.critical(
                    QtGui.QApplication.activeWindow(),
                    'ERROR',
                    'You can not change the DF to an annotation where one already exists',
                    QtGui.QMessageBox.StandardButton.Abort )
            
            elif annotationObj != data.annotation :               
                # First Remove
                annotationObj.removeObject(obj)
                annotationObj.DF = None
                # Then Add to the new annotation
                data.annotation.addObject(obj)
                data.annotation.DF = obj
               
                remove = True
            
            for l in getAllDatumSystemObjects():
                if l.Primary == obj or l.Secondary == obj or l.Tertiary == obj:
                    l.touch
            
            obj.Label = data.textName
            
            if remove:
                annotationObj.DF = None

        elif "GeometricTolerance" == getType(obj):
            annotationObj = getAnnotationWithGT(obj)
            if annotationObj.Label != data.annotation.Label:
                annotationObj.removeObject(obj)
                gt = annotationObj.GT
                gt.remove(obj)
                annotationObj.GT = gt
                data.annotation.addObject(obj)
                gt = data.annotation.GT
                gt.append(obj)
                data.annotation.GT = gt
                
            obj.Label = data.textName
            obj.Characteristic = data.characteristic.Label
            obj.CharacteristicIcon = data.characteristic.Icon
            obj.CharacteristicCode = data.characteristic.Code
            obj.ToleranceValue = data.toleranceValue
            obj.Circumference = data.circumference
            obj.FeatureControlFrame = data.featureControlFrame
            if hasattr(obj,"FeatureControlFrameCode"):
                if data.featureControlFrame != "":
                    index = ToolTip.index(data.featureControlFrame)
                    obj.FeatureControlFrameCode = Code[index]
                    obj.FeatureControlFrameIcon = Icon[index]
                else:
                    obj.FeatureControlFrameCode = ''
                    obj.FeatureControlFrameIcon = ''
                
            obj.DS = data.datumSystem

        FreeCADGui.Control.closeDialog()
        hideGrid()
        for l in getAllAnnotationObjects():
            l.touch()
        FreeCAD.ActiveDocument.recompute()
        Gui.Control.showDialog( GDTGuiClass() )

    """
        Delete Function
    """
    def deleteFunc(self, obj, data):
        # print("5@xes deleteFunc = {}".format(obj))
        # print("5@xes deleteFunc getType = {}".format(getType(obj)))
        if "AnnotationPlane" == getType(obj):
            ok = True
            for l in getAllAnnotationObjects():
                if l.AP == obj:
                    ok = False
                    break
            if ok:
                FreeCAD.ActiveDocument.removeObject(obj.Name)
            else:
                QtGui.QMessageBox.critical(
                    QtGui.QApplication.activeWindow(),
                    'ERROR',
                    'You can not delete AP in use',
                    QtGui.QMessageBox.StandardButton.Abort )

        elif "DatumSystem" == getType(obj):
            FreeCAD.ActiveDocument.removeObject(obj.Name)

        elif "DatumFeature" == getType(obj):
            for l in getAllDatumSystemObjects():
                if l.Primary == obj:
                    l.Primary = l.Secondary
                    l.Secondary = l.Tertiary
                    l.Tertiary = None
                elif l.Secondary == obj:
                    l.Secondary = l.Tertiary
                    l.Tertiary = None
            for l in getAllAnnotationObjects():
                if l.DF == obj:
                    l.DF = None
                    break
            FreeCAD.ActiveDocument.removeObject(obj.Name)

        elif "GeometricTolerance" == getType(obj):
            for l in getAllAnnotationObjects():
                for gt in l.GT:
                    if gt == obj:
                        gtAux = l.GT
                        gtAux.remove(obj)
                        l.GT = gtAux
                        break
            FreeCAD.ActiveDocument.removeObject(obj.Name)

        FreeCADGui.Control.closeDialog()
        hideGrid()
        for l in getAllAnnotationObjects():
            l.touch()
        FreeCAD.ActiveDocument.recompute()
        Gui.Control.showDialog( GDTGuiClass() )

    def getPos(self, actualValue, List):
        for i in range(len(List)):
            if List[i][0] == actualValue:
                return i

    def reject(self): #close button
        hideGrid()
        FreeCADGui.Control.closeDialog()

    def getStandardButtons(self): #http://forum.freecadweb.org/viewtopic.php?f=10&t=11801
        return 0x00200000 #close button

class textLabelWidget_inv:
    def __init__(self, Text='Label', Mask = None, Data = None, Obj = None):
        self.Text = Text
        self.Mask = Mask
        self.data = Data
        self.obj = Obj

    def generateWidget( self ):
        self.lineEdit = QtGui.QLineEdit()
        if self.Mask != None:
            self.lineEdit.setInputMask(self.Mask)
        self.lineEdit.setText(self.obj.Label)
        self.text = self.obj.Label
        self.lineEdit.textChanged.connect(lambda Txt = self.text: self.valueChanged(Txt))
        return GDTDialog_hbox_inv(self.Text, self.lineEdit)

    def valueChanged(self, argGDT):
        self.data.textName = argGDT.strip()

class fieldLabelButtonWidget_inv:
    def __init__(self, Text='Label', Data = None, Obj = None):
        self.Text = Text
        self.data = Data
        self.obj = Obj

    def generateWidget( self ):
        hbox = QtGui.QHBoxLayout()
        self.data.OffsetValue = self.obj.Offset
        self.DECIMALS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Units").GetInt("Decimals",2)
        self.FORMAT = makeFormatSpec(self.DECIMALS,'Length')
        self.uiloader = FreeCADGui.UiLoader()
        self.inputfield = self.uiloader.createWidget("Gui::InputField")
        self.auxText = displayExternal(self.obj.Offset,self.DECIMALS,'Length',True)
        self.inputfield.setText(self.auxText)
        self.firstAttempt = True
        QtCore.QObject.connect(self.inputfield,QtCore.SIGNAL("valueChanged(double)"),lambda Double = self.auxText: self.valueChanged(Double))

        self.button = QtGui.QPushButton('Visualize')
        self.button.clicked.connect(self.visualizeFunc)
        hbox.addLayout( GDTDialog_hbox(self.Text,self.inputfield) )
        hbox.addStretch(1)
        hbox.addWidget(self.button)
        return hbox

    def valueChanged(self, d):
        self.data.OffsetValue = d
        if self.firstAttempt == False:
            showGrid()
            if hasattr(FreeCADGui,"Snapper"):
                if FreeCADGui.Snapper.grid:
                    FreeCAD.DraftWorkingPlane.alignToPointAndAxis(self.obj.p1, self.obj.Direction, self.data.OffsetValue)
                    FreeCADGui.Snapper.grid.set()
        self.firstAttempt = False

    def visualizeFunc(self):
        showGrid()
        if hasattr(FreeCADGui,"Snapper"):
            if FreeCADGui.Snapper.grid:
                FreeCAD.DraftWorkingPlane.alignToPointAndAxis(self.obj.PointWithOffset, self.obj.Direction, 0)
                FreeCADGui.Snapper.grid.set()
        self.inputfield.setText(self.auxText)

class comboLabelWidget_inv:
    def __init__(self, Text='Label', List=[None], Icons=None, ToolTip = None, Data = None, Obj = None):
        self.Text = Text
        self.List = List
        self.Icons = Icons
        self.ToolTip = ToolTip
        self.data = Data
        self.obj = Obj

    def generateWidget( self ):
        if self.Text == 'Primary:':
            self.k=0
        elif self.Text == 'Secondary:':
            self.k=1
        elif self.Text == 'Tertiary:':
            self.k=2
        elif self.Text == 'Characteristic:':
            self.k=3
        elif self.Text == 'Datum system:':
            self.k=4
        elif self.Text == 'In annotation:':
            self.k=5
        else:
            self.k=6
        self.data.combo[self.k] = QtGui.QComboBox()
        for i in range(len(self.List)):
            if self.List[i] == None:
                self.data.combo[self.k].addItem( '' )
            elif self.Icons != None:
                self.data.combo[self.k].addItem( QtGui.QIcon(self.Icons[i]), self.List[i] )
            else:
                self.data.combo[self.k].addItem( self.List[i].Label )

        if self.ToolTip != None:
            self.data.combo[self.k].setToolTip( self.ToolTip[0] )
        self.updateCurrentItem()
        if self.Text == 'Secondary:' and self.data.combo[self.k].currentIndex() == 0 or self.Text == 'Tertiary:' and self.data.combo[self.k].currentIndex() == 0:
            self.data.combo[self.k].setEnabled(False)
        if self.k == 2:
            self.updateItemsEnabled(self.k)
            if self.data.combo[0].currentIndex() != 0:
                self.data.combo[1].setEnabled(True)
                if self.data.combo[1].currentIndex() != 0:
                    self.data.combo[2].setEnabled(True)
        self.data.combo[self.k].activated.connect(lambda comboIndex = self.data.combo[self.k].currentIndex(): self.updateData(comboIndex))

        return GDTDialog_hbox_inv(self.Text, self.data.combo[self.k])

    def updateCurrentItem(self):
        if self.Text == 'Primary:':
            if self.obj.Primary != None:
                actualValue = self.obj.Primary.Label
                pos = self.getPos(actualValue)
                self.data.combo[self.k].setCurrentIndex(pos)
            self.data.textDS[0] = self.data.combo[self.k].currentText()
            self.data.primary = self.List[self.data.combo[self.k].currentIndex()]
        elif self.Text == 'Secondary:':
            if self.obj.Secondary != None:
                actualValue = self.obj.Secondary.Label
                pos = self.getPos(actualValue)
                self.data.combo[self.k].setCurrentIndex(pos)
            self.data.textDS[1] = self.data.combo[self.k].currentText()
            self.data.secondary = self.List[self.data.combo[self.k].currentIndex()]
        elif self.Text == 'Tertiary:':
            if self.obj.Tertiary != None:
                actualValue = self.obj.Tertiary.Label
                pos = self.getPos(actualValue)
                self.data.combo[self.k].setCurrentIndex(pos)
            self.data.textDS[2] = self.data.combo[self.k].currentText()
            self.data.tertiary = self.List[self.data.combo[self.k].currentIndex()]
        elif self.Text == 'Characteristic:':
            if self.obj.Characteristic != '':
                actualValue = self.obj.Characteristic
                pos = self.getPos(actualValue)
            self.data.combo[self.k].setCurrentIndex(pos)
            self.data.characteristic = makeCharacteristics(self.List[self.data.combo[self.k].currentIndex()])
        elif self.Text == 'Datum system:':
            if self.obj.DS != None:
                actualValue = self.obj.DS.Label
                pos = self.getPos(actualValue)
                self.data.combo[self.k].setCurrentIndex(pos)
            self.data.datumSystem = self.List[self.data.combo[self.k].currentIndex()]
        elif self.Text == 'In annotation:':
            annotationObj = getAnnotationWithDF(self.obj) if "DatumFeature" == getType(self.obj) else getAnnotationWithGT(self.obj)
            if annotationObj != None:
                actualValue = annotationObj.Label
                pos = self.getPos(actualValue)
                self.data.combo[self.k].setCurrentIndex(pos)
            self.data.annotation = self.List[self.data.combo[self.k].currentIndex()]

    def getPos(self, actualValue):
        for i in range(len(self.List)):
            if isinstance(self.List[i],str):
                if self.List[i] == actualValue:
                    return i
            elif self.List[i] == None:
                pass
            elif self.List[i].Label == actualValue:
                return i
                
    # Update of the Data
    def updateData(self, comboIndex):
        if self.ToolTip != None:
            self.data.combo[self.k].setToolTip( self.ToolTip[self.data.combo[self.k].currentIndex()] )
        if self.Text == 'Primary:':
            self.data.textDS[0] = self.data.combo[self.k].currentText()
            self.data.primary = self.List[self.data.combo[self.k].currentIndex()]
            if self.data.combo[self.k].currentIndex() != 0:
                self.data.combo[1].setEnabled(True)
            else:
                self.data.combo[1].setEnabled(False)
                self.data.combo[2].setEnabled(False)
                self.data.combo[1].setCurrentIndex(0)
                self.data.combo[2].setCurrentIndex(0)
                self.data.textDS[1] = ''
                self.data.textDS[2] = ''
                self.data.secondary = None
                self.data.tertiary = None
            self.updateItemsEnabled(self.k)
        elif self.Text == 'Secondary:':
            self.data.textDS[1] = self.data.combo[self.k].currentText()
            self.data.secondary = self.List[self.data.combo[self.k].currentIndex()]
            if self.data.combo[self.k].currentIndex() != 0:
                self.data.combo[2].setEnabled(True)
            else:
                self.data.combo[2].setEnabled(False)
                self.data.combo[2].setCurrentIndex(0)
                self.data.textDS[2] = ''
                self.data.tertiary = None
            self.updateItemsEnabled(self.k)
        elif self.Text == 'Tertiary:':
            self.data.textDS[2] = self.data.combo[self.k].currentText()
            self.data.tertiary = self.List[self.data.combo[self.k].currentIndex()]
            self.updateItemsEnabled(self.k)
        elif self.Text == 'Characteristic:':
            self.data.characteristic = makeCharacteristics(self.List[self.data.combo[self.k].currentIndex()])
        elif self.Text == 'Datum system:':
            self.data.datumSystem = self.List[self.data.combo[self.k].currentIndex()]
        elif self.Text == 'In annotation:':
            self.data.annotation = self.List[self.data.combo[self.k].currentIndex()]

    def updateItemsEnabled(self, comboIndex):
        comboIndex0 = comboIndex
        comboIndex1 = (comboIndex+1) % 3
        comboIndex2 = (comboIndex+2) % 3

        for i in range(self.data.combo[comboIndex0].count()):
            self.data.combo[comboIndex0].model().item(i).setEnabled(True)
        if self.data.combo[comboIndex1].currentIndex() != 0:
            self.data.combo[comboIndex0].model().item(self.data.combo[comboIndex1].currentIndex()).setEnabled(False)
        if self.data.combo[comboIndex2].currentIndex() != 0:
            self.data.combo[comboIndex0].model().item(self.data.combo[comboIndex2].currentIndex()).setEnabled(False)
        for i in range(self.data.combo[comboIndex1].count()):
            self.data.combo[comboIndex1].model().item(i).setEnabled(True)
        if self.data.combo[comboIndex0].currentIndex() != 0:
            self.data.combo[comboIndex1].model().item(self.data.combo[comboIndex0].currentIndex()).setEnabled(False)
        if self.data.combo[comboIndex2].currentIndex() != 0:
            self.data.combo[comboIndex1].model().item(self.data.combo[comboIndex2].currentIndex()).setEnabled(False)
        for i in range(self.data.combo[comboIndex2].count()):
            self.data.combo[comboIndex2].model().item(i).setEnabled(True)
        if self.data.combo[comboIndex0].currentIndex() != 0:
            self.data.combo[comboIndex2].model().item(self.data.combo[comboIndex0].currentIndex()).setEnabled(False)
        if self.data.combo[comboIndex1].currentIndex() != 0:
            self.data.combo[comboIndex2].model().item(self.data.combo[comboIndex1].currentIndex()).setEnabled(False)

class groupBoxWidget_inv:
    def __init__(self, Text='Label', List=[], Data = None, Obj = None):
        self.Text = Text
        self.List = List
        self.data = Data
        self.obj = Obj

    def generateWidget( self ):
        self.group = QtGui.QGroupBox(self.Text)
        vbox = QtGui.QVBoxLayout()
        for l in self.List:
            vbox.addLayout(l.generateWidget())
        self.group.setLayout(vbox)
        return self.group

class fieldLabelComboWidget_inv:
    def __init__(self, Text='Label', List=[''], Circumference = [''], Icons=None, ToolTip = None, Data = None, Obj = None):
        self.Text = Text
        self.List = List
        self.Circumference = Circumference
        self.Icons = Icons
        self.ToolTip = ToolTip
        self.data = Data
        self.obj = Obj

    def generateWidget( self ):
        self.DECIMALS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Units").GetInt("Decimals",2)
        self.FORMAT = makeFormatSpec(self.DECIMALS,'Length')
        self.AFORMAT = makeFormatSpec(self.DECIMALS,'Angle')
        self.uiloader = FreeCADGui.UiLoader()
        self.comboCircumference = QtGui.QComboBox()
        self.combo = QtGui.QComboBox()
        for i in range(len(self.List)):
            if self.Icons != None:
                self.combo.addItem( QtGui.QIcon(self.Icons[i]), self.List[i] )
            else:
                self.combo.addItem( self.List[i] )
        for i in range(len(self.Circumference)):
            self.comboCircumference.addItem(QtGui.QIcon(self.Circumference[i]), '' )
        self.comboCircumference.setSizeAdjustPolicy(QtGui.QComboBox.SizeAdjustPolicy(2))
        self.comboCircumference.setToolTip("Indicates whether the tolerance applies to a given diameter")
        self.combo.setSizeAdjustPolicy(QtGui.QComboBox.SizeAdjustPolicy(2))
        actualValue = self.obj.FeatureControlFrame
        pos = self.getPos(actualValue)
        self.combo.setCurrentIndex(pos)
        self.combo.setToolTip( self.ToolTip[self.combo.currentIndex()] )
        self.updateData()
        self.combo.activated.connect(self.updateData)
        if self.obj.Circumference:
            self.comboCircumference.setCurrentIndex(1)
            self.data.circumference = True
        else:
            self.comboCircumference.setCurrentIndex(0)
            self.data.circumference = False
        self.comboCircumference.activated.connect(self.updateDataCircumference)
        hbox = QtGui.QHBoxLayout()
        self.inputfield = self.uiloader.createWidget("Gui::InputField")
        auxText = displayExternal(self.obj.ToleranceValue,self.DECIMALS,'Length',True)
        self.inputfield.setText(auxText)
        self.data.toleranceValue = self.obj.ToleranceValue
        QtCore.QObject.connect(self.inputfield,QtCore.SIGNAL("valueChanged(double)"),lambda Double = auxText: self.valueChanged(Double))
        hbox.addWidget( QtGui.QLabel(self.Text) )
        hbox.addWidget(self.comboCircumference)
        hbox.addStretch(1)
        hbox.addWidget(self.inputfield)
        hbox.addStretch(1)
        hbox.addWidget(self.combo)
        return hbox

    def getPos(self, actualValue):
        if actualValue == '':
            return 0
        else:
            for i in range(len(self.ToolTip)):
                if self.ToolTip[i] == actualValue:
                    return i

    def updateData(self):
        if self.ToolTip != None:
            self.combo.setToolTip( self.ToolTip[self.combo.currentIndex()] )
        if self.Text == 'Tolerance value:':
            self.data.featureControlFrame = '' if self.combo.currentIndex() == 0 else self.ToolTip[self.combo.currentIndex()]

    def updateDataCircumference(self):
        if self.comboCircumference.currentIndex() != 0:
            self.data.circumference = True
        else:
            self.data.circumference = False

    def valueChanged(self,d):
        self.data.toleranceValue = d

def GDTDialog_hbox_inv( label, inputWidget):
    hbox = QtGui.QHBoxLayout()
    hbox.addWidget( QtGui.QLabel(label) )
    if inputWidget != None:
        hbox.addStretch(1)
        hbox.addWidget(inputWidget)
    return hbox

FreeCADGui.addCommand('dd_inventory', InventoryCommand())
