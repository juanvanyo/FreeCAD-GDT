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
from PySide import QtGui,QtCore
from GDT import *

listOfIcons = [':/dd/icons/datumFeature.svg',':/dd/icons/datumSystem.svg',':/dd/icons/geometricTolerance.svg',':/dd/icons/annotationPlane.svg']

listOfCharacteristics = ['Straightness', 'Flatness', 'Circularity', 'Cylindricity', 'Profile of a line', 'Profile of a surface', 'Perpendicularity', 'Angularity', 'Parallelism', 'Symmetry', 'Position', 'Concentricity','Circular run-out', 'Total run-out']
listOfIconsOfCharacteristic = [':/dd/icons/Characteristic/straightness.svg', ':/dd/icons/Characteristic/flatness.svg', ':/dd/icons/Characteristic/circularity.svg', ':/dd/icons/Characteristic/cylindricity.svg', ':/dd/icons/Characteristic/profileOfALine.svg', ':/dd/icons/Characteristic/profileOfASurface.svg', ':/dd/icons/Characteristic/perpendicularity.svg', ':/dd/icons/Characteristic/angularity.svg', ':/dd/icons/Characteristic/parallelism.svg', ':/dd/icons/Characteristic/symmetry.svg', ':/dd/icons/Characteristic/position.svg', ':/dd/icons/Characteristic/concentricity.svg',':/dd/icons/Characteristic/circularRunOut.svg', ':/dd/icons/Characteristic/totalRunOut.svg']

listOfCharacteristics2 = ['','','','','','','','']
listOfIconsOfFeatureControlFrame = ['', ':/dd/icons/FeatureControlFrame/freeState.svg', ':/dd/icons/FeatureControlFrame/leastMaterialCondition.svg', ':/dd/icons/FeatureControlFrame/maximumMaterialCondition.svg', ':/dd/icons/FeatureControlFrame/projectedToleranceZone.svg', ':/dd/icons/FeatureControlFrame/regardlessOfFeatureSize.svg', ':/dd/icons/FeatureControlFrame/tangentPlane.svg', ':/dd/icons/FeatureControlFrame/unequalBilateral.svg']
listOfToolTips = ['Feature control frame', 'Free state', 'Least material condition', 'Maximum material condition', 'Projected tolerance zone', 'Regardless of feature size', 'Tangent plane', 'Unequal Bilateral']

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

class GDTGuiClass:

    def __init__(self):
        self.widgetsGDT = []
        global inventory
        for i in range(len(inventory)):
            if str(inventory[i][0]).find('1') == 0 or str(inventory[i][0]).find('2') == 0 or str(inventory[i][0]).find('3') == 0 or str(inventory[i][0]).find('4') == 0:
                self.widget = QtGui.QWidget()
                title = inventory[i][1]
                if str(inventory[i][0]).find('3') == 0:
                    iconPath = listOfIconsOfCharacteristic[ inventory[i][2] ]
                else:
                    iconPath = listOfIcons[ inventory[i][0] - 1 ]
                self.widget.setWindowTitle( title )
                self.widget.setWindowIcon( QtGui.QIcon( iconPath ) )
                self.widgetsGDT.append(self.widget)
                self.parent = self.widgetsGDT[i]
                self.dialogWidgets = []
                vbox = QtGui.QVBoxLayout(self.parent)
                hbox = QtGui.QHBoxLayout(self.parent)

                if str(inventory[i][0]).find('1') == 0:
                    self.dialogWidgets.append(textLabelWidget_inv(Text = 'Datum feature:', Mask='>A', Name = True, Parent = self.parent, IndexInv = i))

                if str(inventory[i][0]).find('2') == 0:
                    self.dialogWidgets.append(textLabelWidget_inv(Text = 'Name:', Mask='NNNn', Name = True, Parent = self.parent, IndexInv = i))
                    self.dialogWidgets.append( groupBoxWidget_inv(Text='Constituents', List=[comboLabelWidget_inv(Text='Primary:',List=listDF, Parent = self.parent, IndexInv = i),comboLabelWidget_inv(Text='Secondary:',List=listDF, Parent = self.parent, IndexInv = i), comboLabelWidget_inv(Text='Tertiary:',List=listDF, Parent = self.parent, IndexInv = i)], Parent = self.parent, IndexInv = i) )

                if str(inventory[i][0]).find('3') == 0:
                    self.dialogWidgets.append(textLabelWidget_inv(Text = 'Name:', Mask='NNNn', Name = True, Parent = self.parent, IndexInv = i))
                    self.dialogWidgets.append( comboLabelWidget_inv(Text='Characteristic:', List=listOfCharacteristics, Icons=listOfIconsOfCharacteristic, Parent = self.parent, IndexInv = i) )
                    self.dialogWidgets.append( textLabeCombolWidget_inv(Text='Tolerance value:', Mask='00.00', List=listOfCharacteristics2, Icons=listOfIconsOfFeatureControlFrame, ToolTip=listOfToolTips, Parent = self.parent, IndexInv = i) ) #http://doc.qt.io/qt-5/qlineedit.html#inputMask-prop
                    self.dialogWidgets.append( comboLabelWidget_inv(Text='Datum system:', List=listDS, Parent = self.parent, IndexInv = i) )

                if str(inventory[i][0]).find('4') == 0:
                    self.dialogWidgets.append(textLabelWidget_inv(Text = 'Name:', Mask='NNNn', Name = True, Parent = self.parent, IndexInv = i))


                for widg in self.dialogWidgets:
                    w = widg.generateWidget()
                    if isinstance(w, QtGui.QLayout):
                        vbox.addLayout( w )
                    else:
                        vbox.addWidget( w )

                buttonModify = QtGui.QPushButton('Modify',self.parent)
                buttonModify.clicked.connect(self.modifyFunc)
                buttonDelate = QtGui.QPushButton('Delete',self.parent)
                buttonDelate.clicked.connect(self.deleteFunc)
                hbox.addStretch(1)
                hbox.addWidget( buttonModify )
                hbox.addWidget( buttonDelate )
                hbox.addStretch(1)
                vbox.addLayout(hbox)

                self.widget.setLayout(vbox)

        self.form = self.widgetsGDT

    def modifyFunc(self):
        pass

    def deleteFunc(self):
        pass

    def reject(self): #close button
        FreeCADGui.Control.closeDialog()

    def getStandardButtons(self): #http://forum.freecadweb.org/viewtopic.php?f=10&t=11801
        return 0x00200000 #close button

class textLabelWidget_inv:
    def __init__(self, Text='Label', Mask = None, Name = False, Parent = None, IndexInv = 0):
        self.Text = Text
        self.Mask = Mask
        self.Name = Name
        self.parent = Parent
        self.indexInv = IndexInv

    def generateWidget( self ):
        self.lineEdit = QtGui.QLineEdit(self.parent)
        if self.Mask <> None:
            self.lineEdit.setInputMask(self.Mask)
        global inventory
        self.lineEdit.setText(inventory[self.indexInv][1])
        self.text = inventory[self.indexInv][1]
        if self.Name == True:
            self.lineEdit.textChanged.connect(self.valueChanged1)
        else:
            self.lineEdit.textChanged.connect(self.valueChanged2)
        if self.Name == True:
                textName = self.text[:3].strip()
        else:
            if self.Text == 'Datum feature:':
                textName = self.text.strip()
            else:
                textGDT = self.text.strip()
        return GDTDialog_hbox_inv(self.Text, self.lineEdit, parent2 = self.parent)

    def valueChanged1(self, argGDT):
        self.text = argGDT.strip()
        global textName
        textName = self.text

    def valueChanged2(self, argGDT):
        self.text = argGDT.strip()
        global textName, textGDT, indexGDT
        if self.Text == 'Datum feature:':
            textName = self.text
        else:
            textGDT = self.text

class comboLabelWidget_inv:
    def __init__(self, Text='Label', List=[[0,'']], Icons=None, ToolTip = None, Parent = None, IndexInv = 0):
        self.Text = Text
        self.List = List
        self.Icons = Icons
        self.ToolTip = ToolTip
        self.parent = Parent
        self.indexInv = IndexInv

    def generateWidget( self ):
        global textDS
        textDS = ['','','']
        self.combo = QtGui.QComboBox(self.parent)
        for i in range(len(self.List)):
            if self.Icons <> None:
                if isinstance(self.List[len(self.List)-1], list):
                    self.combo.addItem( QtGui.QIcon(self.Icons[i]), self.List[i][1] )
                else:
                    self.combo.addItem( QtGui.QIcon(self.Icons[i]), self.List[i] )
            else:
                if isinstance(self.List[len(self.List)-1], list):
                    self.combo.addItem( self.List[i][1] )
                else:
                    self.combo.addItem( self.List[i] )
        if self.ToolTip <> None:
            self.combo.setToolTip( self.ToolTip[0] )
        self.updateCurrentIndex(self.indexInv)
        self.updateDate()
        self.combo.activated.connect(self.updateDate)

        return GDTDialog_hbox_inv(self.Text,self.combo, parent2 = self.parent)

    def updateCurrentIndex(self, indexInv):
        if self.Text == 'Primary:':
            if len(inventory[indexInv]) > 2:
                actualValue = inventory[inventory[indexInv][2]][1]
                pos = self.getPos(actualValue)
                self.combo.setCurrentIndex(pos)
            textDS[0] = self.combo.currentText()
            primary = self.List[self.combo.currentIndex()][0]
        elif self.Text == 'Secondary:':
            if len(inventory[indexInv]) > 3:
                actualValue = inventory[inventory[indexInv][3]][1]
                pos = self.getPos(actualValue)
                self.combo.setCurrentIndex(pos)
            textDS[1] = self.combo.currentText()
            secondary = self.List[self.combo.currentIndex()][0]
        elif self.Text == 'Tertiary:':
            if len(inventory[indexInv]) > 4:
                actualValue = inventory[inventory[indexInv][4]][1]
                pos = self.getPos(actualValue)
                self.combo.setCurrentIndex(pos)
            textDS[2] = self.combo.currentText()
            terciary = self.List[self.combo.currentIndex()][0]
        elif self.Text == 'Characteristic:':
            pos = inventory[indexInv][2]
            self.combo.setCurrentIndex(pos)
            characteristic = self.combo.currentIndex()
        elif self.Text == 'Datum system:':
            if inventory[indexInv][5] <> None:
                actualValue = inventory[inventory[indexInv][5]][1]
                pos = self.getPos(actualValue)
                self.combo.setCurrentIndex(pos)
            datumSystem = self.List[self.combo.currentIndex()][0]

    def getPos(self, actualValue):
        for i in range(len(self.List)):
            if self.List[i][1] == actualValue:
                return i

    def updateDate(self):
        global textDS, primary, secondary, terciary, characteristic, datumSystem
        if self.ToolTip <> None:
            self.combo.setToolTip( self.ToolTip[self.combo.currentIndex()] )
        if self.Text == 'Primary:':
            textDS[0] = self.combo.currentText()
            primary = self.List[self.combo.currentIndex()][0]
        elif self.Text == 'Secondary:':
            textDS[1] = self.combo.currentText()
            secondary = self.List[self.combo.currentIndex()][0]
        elif self.Text == 'Tertiary:':
            textDS[2] = self.combo.currentText()
            terciary = self.List[self.combo.currentIndex()][0]
        elif self.Text == 'Characteristic:':
            characteristic = self.combo.currentIndex()
        elif self.Text == 'Datum system:':
            datumSystem = self.List[self.combo.currentIndex()][0]

class groupBoxWidget_inv:
    def __init__(self, Text='Label', List=[], Parent = None, IndexInv = 0):
        self.Text = Text
        self.List = List
        self.parent = Parent
        self.indexInv = IndexInv

    def generateWidget( self ):
        self.group = QtGui.QGroupBox(self.Text,self.parent)
        vbox = QtGui.QVBoxLayout(self.parent)
        for l in self.List:
            vbox.addLayout(l.generateWidget())
        self.group.setLayout(vbox)
        return self.group

class textLabeCombolWidget_inv:
    def __init__(self, Text='Label', Mask=None, List=[''], Icons=None, ToolTip = None, Parent = None, IndexInv = 0):
        self.Text = Text
        self.Mask = Mask
        self.List = List
        self.Icons = Icons
        self.ToolTip = ToolTip
        self.parent = Parent
        self.indexInv = IndexInv

    def generateWidget( self ):
        self.combo = QtGui.QComboBox(self.parent)
        for i in range(len(self.List)):
            if self.Icons <> None:
                self.combo.addItem( QtGui.QIcon(self.Icons[i]), self.List[i] )
            else:
                self.combo.addItem( self.List[i] )
        pos = inventory[self.indexInv][4]
        self.combo.setCurrentIndex(pos)
        if self.ToolTip <> None:
           self.combo.setToolTip( self.ToolTip[self.combo.currentIndex()] )
        self.combo.activated.connect(self.updateDate)
        hbox = QtGui.QHBoxLayout(self.parent)
        self.lineEdit = QtGui.QLineEdit(self.parent)
        if self.Mask <> None:
            self.lineEdit.setInputMask(self.Mask)
        self.lineEdit.setText(inventory[self.indexInv][3])
        self.text = inventory[self.indexInv][3]
        self.lineEdit.textChanged.connect(self.valueChanged)
        textGDT = self.text.strip()
        hbox.addLayout( GDTDialog_hbox(self.Text,self.lineEdit) )
        hbox.addStretch(1)
        hbox.addWidget(self.combo)
        return hbox

    def updateDate(self):
        global featureControlFrame
        if self.ToolTip <> None:
            self.combo.setToolTip( self.ToolTip[self.combo.currentIndex()] )
        if self.Text == 'Tolerance value:':
            featureControlFrame = self.combo.currentIndex()
    def valueChanged(self, argGDT):
        global textGDT
        textGDT = argGDT.strip()

    def updateActiveWidget(self):
        global indexGDT, indexDF, indexDS, indexGT, indexAP, idGDTaux
        if idGDTaux == 1:
            indexGDT = indexDF
        elif idGDTaux == 2:
            indexGDT = indexDS
        if idGDTaux == 3:
            indexGDT=indexGT
        elif idGDTaux == 4:
            indexGDT = indexAP
        else:
            pass
        return indexGDT

def GDTDialog_hbox_inv( label, inputWidget, parent2):
    hbox = QtGui.QHBoxLayout( parent2 )
    hbox.addWidget( QtGui.QLabel(label) )
    if inputWidget <> None:
        hbox.addStretch(1)
        hbox.addWidget(inputWidget)
    return hbox

FreeCADGui.addCommand('dd_inventory', InventoryCommand())
