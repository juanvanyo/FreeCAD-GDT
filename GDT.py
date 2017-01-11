
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

import numpy
import FreeCAD as App
import FreeCAD, FreeCADGui, Part, os
from svgLib_dd import SvgTextRenderer, SvgTextParser
import traceback
import Draft
import Part
from pivy import coin

try:
    from PySide import QtCore,QtGui,QtSvg
except ImportError:
    FreeCAD.Console.PrintMessage("Error: Python-pyside package must be installed on your system to use the Geometric Dimensioning & Tolerancing module.")

__dir__ = os.path.dirname(__file__)
iconPath = os.path.join( __dir__, 'Gui','Resources', 'icons' )
FontPath = os.path.join( __dir__, 'Fonts/')
path_dd_resources =  os.path.join( os.path.dirname(__file__), 'Gui', 'Resources', 'dd_resources.rcc')
resourcesLoaded = QtCore.QResource.registerResource(path_dd_resources)
assert resourcesLoaded

indexGDT = 1
indexDF = 1
indexDS = 1
indexGT = 1
indexAP = 1
idGDTaux = 0 #Consultar la manera correcta de hacerlo
textName = ''
textGDT = ''
textDS = ['','','']
listDF = [[None,'']]
listDS = [[None,'']]
listGT = []
listAP = []

inventory = []
indexInventory = 0
primary = None
secondary = None
tertiary = None
characteristic = 0
toleranceValue = 0
featureControlFrame = 0
datumSystem = 0
annotationPlane = 'Annotation Plane'

combo = ['','','','','']
checkBoxState = True
auxDictionaryDS=[]
for i in range(100):
    auxDictionaryDS.append('DS'+str(i))

class GDTWidget:
    def __init__(self):
        self.dialogWidgets = []

    def activate( self, idGDT=0, dialogTitle='GD&T Widget', dialogIconPath=':/dd/icons/GDT.svg', endFunction=None, dictionary=None):
        self.dialogTitle=dialogTitle
        self.dialogIconPath = dialogIconPath
        self.endFunction = endFunction
        self.dictionary = dictionary
        self.idGDT=idGDT
        global idGDTaux, combo
        idGDTaux = idGDT
        combo = ['','','','','']
        extraWidgets = []
        if dictionary <> None:
            extraWidgets.append(textLabelWidget('Name:','NNNn', self.dictionary, Name = True)) #http://doc.qt.io/qt-5/qlineedit.html#inputMask-prop
        else:
            extraWidgets.append(textLabelWidget('Name:','NNNn', Name = True))
        self.taskDialog = GDTDialog( dialogTitle, dialogIconPath, extraWidgets + self.dialogWidgets)
        FreeCADGui.Control.showDialog( self.taskDialog )

class GDTDialog:
    def __init__(self, title, iconPath, dialogWidgets):
        self.initArgs = title, iconPath, dialogWidgets
        self.createForm()

    def createForm(self):
        title, iconPath, dialogWidgets = self.initArgs
        self.form = GDTGuiClass( title, dialogWidgets )
        self.form.setWindowTitle( title )
        self.form.setWindowIcon( QtGui.QIcon( iconPath ) )

    def reject(self): #close button
        FreeCADGui.Control.closeDialog()

    def getStandardButtons(self): #http://forum.freecadweb.org/viewtopic.php?f=10&t=11801
        return 0x00200000 #close button

class GDTGuiClass(QtGui.QWidget):

    def __init__(self, title, dialogWidgets):
        super(GDTGuiClass, self).__init__()
        self.dd_dialogWidgets = dialogWidgets
        self.title = title
        self.initUI( self.title )

    def initUI(self, title):
        vbox = QtGui.QVBoxLayout()
        for widg in self.dd_dialogWidgets:
            w = widg.generateWidget()
            if isinstance(w, QtGui.QLayout):
                vbox.addLayout( w )
            else:
                vbox.addWidget( w )
        hbox = QtGui.QHBoxLayout()
        buttonCreate = QtGui.QPushButton(title)
        buttonCreate.setDefault(True)
        buttonCreate.clicked.connect(self.updateIndex)
        hbox.addStretch(1)
        hbox.addWidget( buttonCreate )
        hbox.addStretch(1)
        vbox.addLayout( hbox )
        self.setLayout(vbox)

    def updateIndex(self):
        global indexGDT, indexDF, indexDS, indexGT, indexAP, idGDTaux, textName, textGDT, listDF, listDS, listGT, listAP, textDS, inventory, indexInventory, primary, secondary, tertiary, characteristic, toleranceValue, featureControlFrame, datumSystem, annotationPlane, auxDictionaryDS
        textName = textName.encode('utf-8')
        if idGDTaux == 1:
            indexDF+=1
            listDF.append( [ indexInventory, textName ] )
            inventory.append( [ idGDTaux, textName, annotationPlane ] )
            if checkBoxState:
                listDS.append( [ indexInventory+1, auxDictionaryDS[indexDS] + ': ' + textName ] )
                inventory.append( [ 2, auxDictionaryDS[indexDS] + ': ' + textName, indexInventory ] )
                indexInventory+=1
                indexDS+=1

        elif idGDTaux == 2:
            separator = ' | '
            indexDS+=1
            if textDS[0] <> '':
                if textDS[1] <> '':
                    if textDS[2] <> '':
                        listDS.append( [ indexInventory, textName + ': ' + separator.join(textDS) ] )
                        inventory.append( [ idGDTaux, textName + ': ' + separator.join(textDS), primary, secondary, tertiary ] )
                    else:
                        listDS.append( [ indexInventory, textName + ': ' + separator.join([textDS[0], textDS[1]]) ] )
                        inventory.append( [ idGDTaux, textName + ': ' + separator.join([textDS[0], textDS[1]]), primary, secondary ] )
                else:
                    listDS.append( [ indexInventory, textName + ': ' + textDS[0] ] )
                    inventory.append( [ idGDTaux, textName + ': ' + textDS[0], primary ] )
            else:
                listDS.append( [ indexInventory, textName ] )
                inventory.append( [ idGDTaux, textName ] )
        if idGDTaux == 3:
            indexGT+=1
            listGT.append( [ indexInventory, textName ] )
            toleranceValue = textGDT
            inventory.append( [ idGDTaux, textName, characteristic, toleranceValue, featureControlFrame, datumSystem, annotationPlane ] )
        elif idGDTaux == 4:
            indexAP+=1
            listAP.append( [ indexInventory, textName ] )
            inventory.append( [ idGDTaux, textName, annotationPlane ] )
        else:
            pass
        indexInventory+=1
        FreeCADGui.Control.closeDialog()

def GDTDialog_hbox( label, inputWidget):
    hbox = QtGui.QHBoxLayout()
    hbox.addWidget( QtGui.QLabel(label) )
    if inputWidget <> None:
        hbox.addStretch(1)
        hbox.addWidget(inputWidget)
    return hbox

class textLabelWidget:
    def __init__(self, Text='Label', Mask=None, Dictionary = None, Name = False):
        self.Text = Text
        self.Mask = Mask
        self.Dictionary = Dictionary
        self.Name = Name

    def generateWidget( self ):
        self.lineEdit = QtGui.QLineEdit()
        if self.Mask <> None:
            self.lineEdit.setInputMask(self.Mask)
        if self.Dictionary == None:
            self.lineEdit.setText('text')
            self.text = 'text'
        else:
            self.updateActiveWidget()
            global textName, textGDT, indexGDT
            if indexGDT > len(self.Dictionary)-1:
                indexGDT = len(self.Dictionary)-1
            self.lineEdit.setText(self.Dictionary[indexGDT])
            self.text = self.Dictionary[indexGDT]
        if self.Name == True:
            self.lineEdit.textChanged.connect(self.valueChanged1)
        else:
            self.lineEdit.textChanged.connect(self.valueChanged2)
        if self.Name == True:
                textName = self.text.strip()
        else:
            if self.Text == 'Datum feature:':
                textName = self.text.strip()
            else:
                textGDT = self.text.strip()
        return GDTDialog_hbox(self.Text,self.lineEdit)

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

    def updateActiveWidget(self):
        global indexGDT, indexDF, indexDS, indexGT, indexAP, idGDTaux
        if idGDTaux == 1:
            indexGDT = indexDF
        elif idGDTaux == 2:
            indexGDT = indexDS
        if idGDTaux == 3:
            indexGDT = indexGT
        elif idGDTaux == 4:
            indexGDT = indexAP
        else:
            pass
        return indexGDT

class comboLabelWidget:
    def __init__(self, Text='Label', List=[[None,'']], Icons=None, ToolTip = None):
        self.Text = Text
        self.List = List
        self.Icons = Icons
        self.ToolTip = ToolTip

    def generateWidget( self ):
        global textDS, combo
        textDS = ['','','']

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
        else:
            self.k=5

        combo[self.k] = QtGui.QComboBox()
        for i in range(len(self.List)):
            if self.Icons <> None:
                if isinstance(self.List[len(self.List)-1], list):
                    combo[self.k].addItem( QtGui.QIcon(self.Icons[i]), self.List[i][1] )
                else:
                    combo[self.k].addItem( QtGui.QIcon(self.Icons[i]), self.List[i] )
            else:
                if isinstance(self.List[len(self.List)-1], list):
                    combo[self.k].addItem( self.List[i][1] )
                else:
                    combo[self.k].addItem( self.List[i] )
        if self.Text == 'Secondary:' or self.Text == 'Tertiary:':
            combo[self.k].setEnabled(False)
        if self.ToolTip <> None:
            combo[self.k].setToolTip( self.ToolTip[0] )
        self.comboIndex = combo[self.k].currentIndex()
        if self.k <> 0 and self.k <> 1:
            self.updateDate(self.comboIndex)
        combo[self.k].activated.connect(lambda comboIndex = self.comboIndex: self.updateDate(self.comboIndex))
        return GDTDialog_hbox(self.Text,combo[self.k])

    def updateDate(self, comboIndex):
        global textDS, primary, secondary, tertiary, characteristic, datumSystem, combo
        if self.ToolTip <> None:
            combo[self.k].setToolTip( self.ToolTip[combo[self.k].currentIndex()] )
        if self.Text == 'Primary:':
            textDS[0] = combo[self.k].currentText()
            primary = self.List[combo[self.k].currentIndex()][0]
            if combo[self.k].currentIndex() <> 0:
                combo[1].setEnabled(True)
            else:
                combo[1].setEnabled(False)
                combo[2].setEnabled(False)
                combo[1].setCurrentIndex(0)
                combo[2].setCurrentIndex(0)
                textDS[1] = ''
                textDS[2] = ''
                secondary = None
                tertiary = None
            self.updateItemsEnabled(self.k)
        elif self.Text == 'Secondary:':
            textDS[1] = combo[self.k].currentText()
            secondary = self.List[combo[self.k].currentIndex()][0]
            if combo[self.k].currentIndex() <> 0:
                combo[2].setEnabled(True)
            else:
                combo[2].setEnabled(False)
                combo[2].setCurrentIndex(0)
                textDS[2] = ''
                tertiary = None
            self.updateItemsEnabled(self.k)
        elif self.Text == 'Tertiary:':
            textDS[2] = combo[self.k].currentText()
            tertiary = self.List[combo[self.k].currentIndex()][0]
            self.updateItemsEnabled(self.k)
        elif self.Text == 'Characteristic:':
            characteristic = combo[self.k].currentIndex()
        elif self.Text == 'Datum system:':
            datumSystem = self.List[combo[self.k].currentIndex()][0]

    def updateItemsEnabled(self, comboIndex):
        global combo
        comboIndex0 = comboIndex
        comboIndex1 = (comboIndex+1) % 3
        comboIndex2 = (comboIndex+2) % 3

        for i in range(combo[comboIndex0].count()):
            combo[comboIndex0].model().item(i).setEnabled(True)
        if combo[comboIndex1].currentIndex() <> 0:
            combo[comboIndex0].model().item(combo[comboIndex1].currentIndex()).setEnabled(False)
        if combo[comboIndex2].currentIndex() <> 0:
            combo[comboIndex0].model().item(combo[comboIndex2].currentIndex()).setEnabled(False)
        for i in range(combo[comboIndex1].count()):
            combo[comboIndex1].model().item(i).setEnabled(True)
        if combo[comboIndex0].currentIndex() <> 0:
            combo[comboIndex1].model().item(combo[comboIndex0].currentIndex()).setEnabled(False)
        if combo[comboIndex2].currentIndex() <> 0:
            combo[comboIndex1].model().item(combo[comboIndex2].currentIndex()).setEnabled(False)
        for i in range(combo[comboIndex2].count()):
            combo[comboIndex2].model().item(i).setEnabled(True)
        if combo[comboIndex0].currentIndex() <> 0:
            combo[comboIndex2].model().item(combo[comboIndex0].currentIndex()).setEnabled(False)
        if combo[comboIndex1].currentIndex() <> 0:
            combo[comboIndex2].model().item(combo[comboIndex1].currentIndex()).setEnabled(False)

class groupBoxWidget:
    def __init__(self, Text='Label', List=[]):
        self.Text = Text
        self.List = List

    def generateWidget( self ):
        self.group = QtGui.QGroupBox(self.Text)
        vbox = QtGui.QVBoxLayout()
        for l in self.List:
            vbox.addLayout(l.generateWidget())
        self.group.setLayout(vbox)
        return self.group

class textLabeCombolWidget:
    def __init__(self, Text='Label', Mask=None, Dictionary = None, List=[''], Icons=None, ToolTip = None):
        self.Text = Text
        self.Mask = Mask
        self.Dictionary = Dictionary
        self.List = List
        self.Icons = Icons
        self.ToolTip = ToolTip

    def generateWidget( self ):
        self.combo = QtGui.QComboBox()
        for i in range(len(self.List)):
            if self.Icons <> None:
                self.combo.addItem( QtGui.QIcon(self.Icons[i]), self.List[i] )
            else:
                self.combo.addItem( self.List[i] )
        if self.ToolTip <> None:
           self.combo.setToolTip( self.ToolTip[0] )
        self.combo.activated.connect(self.updateDate)
        hbox = QtGui.QHBoxLayout()
        self.lineEdit = QtGui.QLineEdit()
        if self.Mask <> None:
            self.lineEdit.setInputMask(self.Mask)
        if self.Dictionary == None:
            self.lineEdit.setText('text')
            self.text = 'text'
        else:
            self.updateActiveWidget()
            global textName, textGDT, indexGDT
            if indexGDT > len(self.Dictionary)-1:
                indexGDT = len(self.Dictionary)-1
            self.lineEdit.setText(self.Dictionary[indexGDT])
            self.text = self.Dictionary[indexGDT]
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
            indexGDT = indexGT
        elif idGDTaux == 4:
            indexGDT = indexAP
        else:
            pass
        return indexGDT

class CheckBoxWidget:
    def __init__(self, Text='Label'):
        self.Text = Text

    def generateWidget( self ):
        self.checkBox = QtGui.QCheckBox(self.Text)
        self.checkBox.setChecked(True)
        global checkBoxState
        checkBoxState = True
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.checkBox)
        hbox.addStretch(1)
        self.checkBox.stateChanged.connect(self.updateState)
        return hbox

    def updateState(self):
        global checkBoxState
        if self.checkBox.isChecked():
            checkBoxState = True
        else:
            checkBoxState = False

class LabeledLine(Draft._DraftObject):
    def __init__(self, obj):
        Draft._DraftObject.__init__(self,obj,"LabeledLine")
        obj.addProperty("App::PropertyLinkList","Components","Draft",
                        "The line and text components of this labeled line")

    def onChanged(self, fp, prop):
        if prop in ["Components"]:
            self.createGeometry(fp)

    def execute(self, fp):
        self.createGeometry(fp)

    def createGeometry(self,fp):
        plm = fp.Placement
        shps = []
        for c in fp.Components:
            shps.append(c.Shape)
        if shps:
            shape = Part.makeCompound(shps)
            fp.Shape = shape
        fp.Placement = plm


class helpGDTCommand:
    def Activated(self):
        # QtGui.QMessageBox.information(
        #     QtGui.qApp.activeWindow(),
        #     'Geometric Dimensioning & Tolerancing Help',
        #     'Developing...' )
        # set the parameters
        sizeOfLine = 5
        s=FreeCADGui.Selection.getSelectionEx()
        obj=s[0]
        faceSel = obj.SubObjects[0]
        Direction = faceSel.normalAt(0,0)
        P1 = faceSel.CenterOfMass
        P2 = Direction * sizeOfLine + P1
        Direction2 = Direction
        for i in range(3):
            if Direction[i] == 0:
                Direction2[i] = 1.0
            else:
                Direction2[i] = 0.0
        P3 = Direction2 * sizeOfLine + P2
        LabelText = "Some Text for My Line"
        FontName = 'Arial.ttf'
        FontFile = FontPath+FontName
        Size = 1.0
        myLine1 = Draft.makeLine(P1,P2)
        myLine2 = Draft.makeLine(P2,P3)
        myString = Draft.makeShapeString(LabelText,FontFile,Size)
        myString.Placement.move(P3)
        #myString.Placement.move(myLine.Shape.BoundBox.Center)

        # make the feature
        feat = FreeCAD.ActiveDocument.addObject("Part::Part2DObjectPython","LabeledLine")
        LabeledLine(feat)
        feat.Components = [myLine1,myLine2,myString]
        Draft._ViewProviderDraft(feat.ViewObject)
    def GetResources(self):
        return {
            'Pixmap' : ':/dd/icons/helpGDT.svg',
            'MenuText': 'Help',
            'ToolTip': 'Help'
            }

FreeCADGui.addCommand('dd_helpGDT', helpGDTCommand())
