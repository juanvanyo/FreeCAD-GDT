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

textNameList = []
textDSList = []
primaryList = []
secondaryList = []
tertiaryList = []

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
        global textDSList, primaryList, secondaryList, tertiaryList, textNameList, inventory
        self.widgetsGDT = []
        primaryList = []
        secondaryList = []
        tertiaryList = []
        textNameList = []
        textDSList = []
        for i in range(len(inventory)):
            if str(inventory[i][0]).find('1') == 0 or str(inventory[i][0]).find('2') == 0 or str(inventory[i][0]).find('3') == 0 or str(inventory[i][0]).find('4') == 0:
                self.widget = QtGui.QWidget()
                if len(inventory[i][1]) > 4:
                    textNameList.append((inventory[i][1])[:inventory[i][1].find(':')])
                else:
                    textNameList.append((inventory[i][1]))
                if inventory[i][0] == 2:
                    textDS=['','','']
                    separator = ' | '
                    if len(inventory[i]) > 2:
                        textDS[0] = inventory[inventory[i][2]][1]
                        if len(inventory[i]) > 3:
                            textDS[1] = inventory[inventory[i][3]][1]
                            if len(inventory[i]) > 4:
                                textDS[2] = inventory[inventory[i][4]][1]
                                inventory[i][1] = textNameList[i]+ ': ' + separator.join(textDS)
                            else:
                                inventory[i][1] = textNameList[i]+ ': ' + separator.join([textDS[0], textDS[1]])
                        else:
                            inventory[i][1] = textNameList[i]+ ': ' + textDS[0]
                    else:
                        inventory[i][1] = textNameList[i]
                self.widget.title = inventory[i][1]
                primaryList.append(0)
                secondaryList.append(0)
                tertiaryList.append(0)
                textDSList.append(['','',''])
                if str(inventory[i][0]).find('3') == 0:
                    iconPath = listOfIconsOfCharacteristic[ inventory[i][2] ]
                else:
                    iconPath = listOfIcons[ inventory[i][0] - 1 ]
                self.widget.setWindowTitle( self.widget.title )
                self.widget.setWindowIcon( QtGui.QIcon( iconPath ) )
                self.widgetsGDT.append(self.widget)
                self.widgetsGDT[i].gdtID = inventory[i][0]
                self.parent = self.widgetsGDT[i]
                self.dialogWidgets = []
                vbox = QtGui.QVBoxLayout(self.parent)
                hbox = QtGui.QHBoxLayout(self.parent)

                if str(inventory[i][0]).find('1') == 0:
                    self.dialogWidgets.append(textLabelWidget_inv(Text = 'Datum feature:', Mask='>A', Parent = self.parent, IndexInv = i))

                if str(inventory[i][0]).find('2') == 0:
                    self.dialogWidgets.append(textLabelWidget_inv(Text = 'Name:', Mask='NNNn', Parent = self.parent, IndexInv = i))
                    self.dialogWidgets.append( groupBoxWidget_inv(Text='Constituents', List=[comboLabelWidget_inv(Text='Primary:',List=listDF, Parent = self.parent, IndexInv = i),comboLabelWidget_inv(Text='Secondary:',List=listDF, Parent = self.parent, IndexInv = i), comboLabelWidget_inv(Text='Tertiary:',List=listDF, Parent = self.parent, IndexInv = i)], Parent = self.parent, IndexInv = i) )

                if str(inventory[i][0]).find('3') == 0:
                    self.dialogWidgets.append(textLabelWidget_inv(Text = 'Name:', Mask='NNNn', Parent = self.parent, IndexInv = i))
                    self.dialogWidgets.append( comboLabelWidget_inv(Text='Characteristic:', List=listOfCharacteristics, Icons=listOfIconsOfCharacteristic, Parent = self.parent, IndexInv = i) )
                    self.dialogWidgets.append( textLabeCombolWidget_inv(Text='Tolerance value:', Mask='00.00', List=listOfCharacteristics2, Icons=listOfIconsOfFeatureControlFrame, ToolTip=listOfToolTips, Parent = self.parent, IndexInv = i) ) #http://doc.qt.io/qt-5/qlineedit.html#inputMask-prop
                    self.dialogWidgets.append( comboLabelWidget_inv(Text='Datum system:', List=listDS, Parent = self.parent, IndexInv = i) )

                if str(inventory[i][0]).find('4') == 0:
                    self.dialogWidgets.append(textLabelWidget_inv(Text = 'Name:', Mask='NNNn', Parent = self.parent, IndexInv = i))

                for widg in self.dialogWidgets:
                    w = widg.generateWidget()
                    if isinstance(w, QtGui.QLayout):
                        vbox.addLayout( w )
                    else:
                        vbox.addWidget( w )

                buttonModify = QtGui.QPushButton('Modify')
                buttonModify.clicked.connect(lambda aux = i: self.modifyFunc(aux))
                buttonDelate = QtGui.QPushButton('Delete')
                buttonDelate.clicked.connect(lambda aux = i: self.deleteFunc(aux))
                hbox.addStretch(1)
                hbox.addWidget( buttonModify )
                hbox.addWidget( buttonDelate )
                hbox.addStretch(1)
                vbox.addLayout(hbox)
                self.widget.setLayout(vbox)
        self.form = self.widgetsGDT

    def modifyFunc(self,i):
        global inventory, listDF, listDS, primaryList, secondaryList, tertiaryList, textNameList
        if self.widgetsGDT[i].gdtID == 1:
            inventory[i] = [self.widgetsGDT[i].gdtID, textNameList[i], annotationPlane]
            pos = self.getPos(i, listDF)
            listDF[pos] = [i, textNameList[i]]
        elif self.widgetsGDT[i].gdtID == 2:
            pos = self.getPos(i, listDS)
            separator = ' | '
            if textDSList[i][0] <> '':
                if textDSList[i][1] <> '':
                    if textDSList[i][2] <> '':
                        listDS[pos] = [ i, textNameList[i] + ': ' + separator.join(textDSList[i]) ]
                        inventory[i] = [ self.widgetsGDT[i].gdtID, textNameList[i] + ': ' + separator.join(textDSList[i]), primaryList[i], secondaryList[i], tertiaryList[i] ]
                    else:
                        listDS[pos] = [ i, textNameList[i] + ': ' + separator.join([textDSList[i][0], textDSList[i][1]]) ]
                        inventory[i] = [ self.widgetsGDT[i].gdtID, textNameList[i] + ': ' + separator.join([textDSList[i][0], textDSList[i][1]]), primaryList[i], secondaryList[i] ]
                else:
                    listDS[pos] = [ i, textNameList[i] + ': ' + textDSList[i][0] ]
                    inventory[i] = [ self.widgetsGDT[i].gdtID, textNameList[i] + ': ' + textDSList[i][0], primaryList[i] ]
            else:
                listDS[pos] = [ i, textNameList[i] ]
                inventory[i] = [ self.widgetsGDT[i].gdtID, textNameList[i] ]
        elif self.widgetsGDT[i].gdtID == 3:
            inventory[i][1] = textNameList[i]
        elif self.widgetsGDT[i].gdtID == 4:
            inventory[i][1] = textNameList[i]
        else:
            pass
        FreeCADGui.Control.closeDialog()
        Gui.Control.showDialog( GDTGuiClass() )

    def getPos(self, actualValue, List):
        for i in range(len(List)):
            if List[i][0] == actualValue:
                return i

    def deleteFunc(self,i):
        global inventory
        if self.widgetsGDT[i].gdtID == 1:
            FreeCAD.Console.PrintMessage('DF')
        elif self.widgetsGDT[i].gdtID == 2:
            FreeCAD.Console.PrintMessage('DS')
        elif self.widgetsGDT[i].gdtID == 3:
            FreeCAD.Console.PrintMessage('GT')
        elif self.widgetsGDT[i].gdtID == 4:
            FreeCAD.Console.PrintMessage('AP')
        else:
            pass

    def reject(self): #close button
        FreeCADGui.Control.closeDialog()

    def getStandardButtons(self): #http://forum.freecadweb.org/viewtopic.php?f=10&t=11801
        return 0x00200000 #close button

class textLabelWidget_inv:
    def __init__(self, Text='Label', Mask = None, Parent = None, IndexInv = 0):
        self.Text = Text
        self.Mask = Mask
        self.parent = Parent
        self.indexInv = IndexInv

    def generateWidget( self ):
        self.lineEdit = QtGui.QLineEdit(self.parent)
        if self.Mask <> None:
            self.lineEdit.setInputMask(self.Mask)
        self.lineEdit.setText(inventory[self.indexInv][1])
        self.text = inventory[self.indexInv][1]
        self.lineEdit.textChanged.connect(lambda Txt = self.text, aux = self.indexInv: self.valueChanged(Txt, aux))
        return GDTDialog_hbox_inv(self.Text, self.lineEdit, parent = self.parent)

    def valueChanged(self, argGDT, i):
        global textNameList
        textNameList[i] = argGDT.strip()

class comboLabelWidget_inv:
    def __init__(self, Text='Label', List=[[0,'']], Icons=None, ToolTip = None, Parent = None, IndexInv = 0):
        self.Text = Text
        self.List = List
        self.Icons = Icons
        self.ToolTip = ToolTip
        self.parent = Parent
        self.IndexInv = IndexInv

    def generateWidget( self ):

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
        self.updateCurrentIndex(self.IndexInv)
        self.comboIndex = self.combo.currentText()
        self.updateDate(comboIndex = self.comboIndex, IndexInv = self.IndexInv)
        self.combo.activated.connect(lambda comboIndex = self.comboIndex, IndexInv = self.IndexInv: self.updateDate(comboIndex, IndexInv))

        return GDTDialog_hbox_inv(self.Text,self.combo, parent = self.parent)

    def updateCurrentIndex(self, IndexInv):
        global textDSList, primaryList, secondaryList, tertiaryList
        if self.Text == 'Primary:':
            if len(inventory[IndexInv]) > 2:
                actualValue = inventory[inventory[IndexInv][2]][1]
                pos = self.getPos(actualValue)
                self.combo.setCurrentIndex(pos)
            textDSList[IndexInv][0] = self.combo.currentText()
            primaryList[IndexInv] = self.List[self.combo.currentIndex()][0]
        elif self.Text == 'Secondary:':
            if len(inventory[IndexInv]) > 3:
                actualValue = inventory[inventory[IndexInv][3]][1]
                pos = self.getPos(actualValue)
                self.combo.setCurrentIndex(pos)
            textDSList[IndexInv][1] = self.combo.currentText()
            secondaryList[IndexInv] = self.List[self.combo.currentIndex()][0]
        elif self.Text == 'Tertiary:':
            if len(inventory[IndexInv]) > 4:
                actualValue = inventory[inventory[IndexInv][4]][1]
                pos = self.getPos(actualValue)
                self.combo.setCurrentIndex(pos)
            textDSList[IndexInv][2] = self.combo.currentText()
            tertiaryList[IndexInv] = self.List[self.combo.currentIndex()][0]
        elif self.Text == 'Characteristic:':
            pos = inventory[IndexInv][2]
            self.combo.setCurrentIndex(pos)
            characteristic = self.combo.currentIndex()
        elif self.Text == 'Datum system:':
            if inventory[IndexInv][5] <> None:
                actualValue = inventory[inventory[IndexInv][5]][1]
                pos = self.getPos(actualValue)
                self.combo.setCurrentIndex(pos)
            datumSystem = self.List[self.combo.currentIndex()][0]

    def getPos(self, actualValue):
        for i in range(len(self.List)):
            if self.List[i][1] == actualValue:
                return i

    def updateDate(self, comboIndex, IndexInv):
        global textDSList, primaryList, secondaryList, tertiaryList, characteristic, datumSystem
        if self.ToolTip <> None:
            self.combo.setToolTip( self.ToolTip[self.combo.currentIndex()] )
        if self.Text == 'Primary:':
            textDSList[IndexInv][0] = self.combo.currentText()
            primaryList[IndexInv] = self.List[self.combo.currentIndex()][0]
        elif self.Text == 'Secondary:':
            textDSList[IndexInv][1] = self.combo.currentText()
            secondaryList[IndexInv] = self.List[self.combo.currentIndex()][0]
        elif self.Text == 'Tertiary:':
            textDSList[IndexInv][2] = self.combo.currentText()
            tertiaryList[IndexInv] = self.List[self.combo.currentIndex()][0]
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

def GDTDialog_hbox_inv( label, inputWidget, parent):
    hbox = QtGui.QHBoxLayout( parent )
    hbox.addWidget( QtGui.QLabel(label) )
    if inputWidget <> None:
        hbox.addStretch(1)
        hbox.addWidget(inputWidget)
    return hbox

FreeCADGui.addCommand('dd_inventory', InventoryCommand())
