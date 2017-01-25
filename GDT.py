
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

__title__="FreeCAD GDT Workbench"
__author__ = "Juan Vanyo Cerda <juavacer@inf.upv.es>"
__url__ = "http://www.freecadweb.org"

# Description of tool

import numpy
import FreeCAD as App
import FreeCAD, math, sys, os, DraftVecUtils, Draft_rc
from FreeCAD import Vector
from svgLib_dd import SvgTextRenderer, SvgTextParser
import traceback
import Draft
import Part
from pivy import coin
if FreeCAD.GuiUp:
    import FreeCADGui, WorkingPlane
    gui = True
else:
    print("FreeCAD Gui not present. GDT module will have some features disabled.")
    gui = False

try:
    from PySide import QtCore,QtGui,QtSvg
except ImportError:
    FreeCAD.Console.PrintMessage("Error: Python-pyside package must be installed on your system to use the Geometric Dimensioning & Tolerancing module.")

#---------------------------------------------------------------------------
# General functions
#---------------------------------------------------------------------------

def stringencodecoin(ustr):
    """stringencodecoin(str): Encodes a unicode object to be used as a string in coin"""
    try:
        from pivy import coin
        coin4 = coin.COIN_MAJOR_VERSION >= 4
    except (ImportError, AttributeError):
        coin4 = False
    if coin4:
        return ustr.encode('utf-8')
    else:
        return ustr.encode('latin1')

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
idGDTaux = 0
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
toleranceValue = 0.0
featureControlFrame = 0
datumSystem = 0
annotationPlane = 0
offsetValue = 0
P1 = FreeCAD.Vector(0.0,0.0,0.0)
Direction = FreeCAD.Vector(0.0,0.0,0.0)

combo = ['','','','','','']
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
        combo = ['','','','','','']
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
        if hasattr(FreeCADGui,"Snapper"):
            if FreeCADGui.Snapper.grid:
                if FreeCADGui.Snapper.grid.Visible:
                    FreeCADGui.Snapper.grid.off()
                    FreeCADGui.Snapper.forceGridOff=True
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
        global indexGDT, indexDF, indexDS, indexGT, indexAP, idGDTaux, textName, textGDT, listDF, listDS, listGT, listAP, textDS, inventory, indexInventory, primary, secondary, tertiary, characteristic, toleranceValue, featureControlFrame, datumSystem, annotationPlane, auxDictionaryDS, P1, Direction, offsetValue
        self.textName = textName.encode('utf-8')
        self.view = Draft.get3DView()
        self.point = FreeCAD.Vector(0.0,0.0,0.0)

        def cb(point):
            if point:
                self.point = point
                FreeCAD.Console.PrintMessage('Punto seleccionado: ' + str(self.point) + '\n')
                plotLines()

        def plotLines():
            sizeOfLine = 1.0
            aux = FreeCAD.Vector(0.0,0.0,0.0)
            P2 = FreeCAD.Vector(0.0,0.0,0.0)
            posToModify = 0
            for i in range(3):
                aux[i] = Direction[i]*self.point[i]
                if aux[i] == 0.0:
                    P2[i] = P1[i]
                else:
                    posToModify = i

            P2[posToModify] = aux[posToModify]
            P3 = FreeCAD.Vector(self.point[0],P2[1],P2[2]) # Revisar este punto
            Size = 1.0
            points = [P1,P2,P3]
            P4 = FreeCAD.Vector(P3[0],P3[1]-sizeOfLine,P3[2])
            points.append(P4)
            P5 = FreeCAD.Vector(P3[0],P3[1]+sizeOfLine,P3[2])
            points.append(P5)
            P6 = FreeCAD.Vector(P5[0]+sizeOfLine*3,P5[1],P5[2])
            points.append(P6)
            P7 = FreeCAD.Vector(P6[0],P6[1]-sizeOfLine*2,P6[2])
            points.append(P7)
            P8 = FreeCAD.Vector(P7[0]-sizeOfLine,P7[1],P7[2])
            points.append(P8)
            P9 = FreeCAD.Vector(P8[0]-sizeOfLine,P8[1],P8[2])
            points.append(P9)
            P10 = FreeCAD.Vector(P9[0]-sizeOfLine,P9[1],P9[2])
            points.append(P10)
            P11=P9
            points.append(P11)
            h=math.sqrt(sizeOfLine*sizeOfLine+(sizeOfLine/2)*(sizeOfLine/2))
            P12 = FreeCAD.Vector(P11[0]+sizeOfLine/2,P11[1]-h,P11[2])
            points.append(P12)
            P13=P8
            points.append(P13)
            P14=P12
            points.append(P14)
            P15 = FreeCAD.Vector(P14[0],P11[1]-sizeOfLine*3,P11[2])
            points.append(P15)
            P16 = FreeCAD.Vector(P15[0]+sizeOfLine,P15[1],P15[2])
            points.append(P16)
            P17 = FreeCAD.Vector(P16[0],P16[1]-sizeOfLine*2,P15[2])
            points.append(P17)
            P18 = FreeCAD.Vector(P17[0]-sizeOfLine*2,P17[1],P17[2])
            points.append(P18)
            P19 = FreeCAD.Vector(P18[0],P18[1]+sizeOfLine*2,P18[2])
            points.append(P19)
            P20=P15
            points.append(P20)

            PText = FreeCAD.Vector(P18[0]+sizeOfLine/5,P18[1]+sizeOfLine/5,P18[2])
            myWire = Draft.makeWire(points,closed=False,face=True,support=None)
            myWire.ViewObject.LineColor = (1.0, 0.65, 0.0)
            myLabel = Draft.makeText(self.textName,point=PText,screen=False) # If screen is True, the text always faces the view direction.
            myLabel.ViewObject.TextColor = (1.0, 0.65, 0.0)
            myLabel.ViewObject.FontSize = 2.2
            # FreeCAD.Console.PrintMessage('Direction: ' + str(Direction) + '\n')
            # FreeCAD.Console.PrintMessage('P1: ' + str(P1) + '\n')
            # FreeCAD.Console.PrintMessage('P2: ' + str(P2) + '\n')
            # FreeCAD.Console.PrintMessage('P3: ' + str(P3) + '\n')
            # FreeCAD.Console.PrintMessage('P4: ' + str(P4) + '\n')
            if hasattr(FreeCADGui,"Snapper"):
                if FreeCADGui.Snapper.grid:
                    if FreeCADGui.Snapper.grid.Visible:
                        FreeCADGui.Snapper.grid.off()
                        FreeCADGui.Snapper.forceGridOff=True

        if idGDTaux == 1:
            indexDF+=1
            listDF.append( [ indexInventory, self.textName ] )
            inventory.append( [ idGDTaux, self.textName, annotationPlane ] )
            auxIndexInventory = indexInventory
            if checkBoxState:
                listDS.append( [ indexInventory+1, auxDictionaryDS[indexDS] + ': ' + self.textName ] )
                inventory.append( [ 2, auxDictionaryDS[indexDS] + ': ' + self.textName, indexInventory ] )
                indexInventory+=1
                indexDS+=1
            # adding callback functions
            myPlane = WorkingPlane.plane()
            # Direction = FreeCADGui.Selection.getSelectionEx()[0].SubObjects[0].normalAt(0,0) # normalAt
            Direction = FreeCADGui.Selection.getSelectionEx()[0].SubObjects[0].Surface.Axis # to Axis    .normalAt(0,0) # normalAt
            PCenter = FreeCADGui.Selection.getSelectionEx()[0].SubObjects[0].CenterOfMass
            PCenterAP = inventory[inventory[auxIndexInventory][2]][2]
            DirectionAP = inventory[inventory[auxIndexInventory][2]][3]
            OffsetAP = inventory[inventory[auxIndexInventory][2]][4]
            PointAP = PCenterAP + DirectionAP*OffsetAP
            P1=PCenter.projectToPlane(PointAP,DirectionAP)
            # FreeCAD.Console.PrintMessage('Direction: ' + str(Direction) + '\n')
            # FreeCAD.Console.PrintMessage('DirectionAP: ' + str(inventory[inventory[auxIndexInventory][2]][3]) + '\n')
            # FreeCAD.Console.PrintMessage('Perpendicular: ' + str(Perpendicular) + '\n')
            # FreeCAD.Console.PrintMessage('P1AP: ' + str(inventory[inventory[auxIndexInventory][2]][2]) + '\n')
            # FreeCAD.Console.PrintMessage('PCenter: ' + str(PCenter) + '\n')
            # self.callbackClick = self.view.addEventCallbackPivy(coin.SoMouseButtonEvent.getClassTypeId(),click)
            FreeCADGui.Snapper.getPoint(callback=cb)


        elif idGDTaux == 2:
            separator = ' | '
            indexDS+=1
            if textDS[0] <> '':
                if textDS[1] <> '':
                    if textDS[2] <> '':
                        listDS.append( [ indexInventory, self.textName + ': ' + separator.join(textDS) ] )
                        inventory.append( [ idGDTaux, self.textName + ': ' + separator.join(textDS), primary, secondary, tertiary ] )
                    else:
                        listDS.append( [ indexInventory, self.textName + ': ' + separator.join([textDS[0], textDS[1]]) ] )
                        inventory.append( [ idGDTaux, self.textName + ': ' + separator.join([textDS[0], textDS[1]]), primary, secondary ] )
                else:
                    listDS.append( [ indexInventory, self.textName + ': ' + textDS[0] ] )
                    inventory.append( [ idGDTaux, self.textName + ': ' + textDS[0], primary ] )
            else:
                listDS.append( [ indexInventory, self.textName ] )
                inventory.append( [ idGDTaux, self.textName ] )
        if idGDTaux == 3:
            indexGT+=1
            listGT.append( [ indexInventory, self.textName ] )
            inventory.append( [ idGDTaux, self.textName, characteristic, toleranceValue, featureControlFrame, datumSystem, annotationPlane ] )
        elif idGDTaux == 4:
            indexAP+=1
            listAP.append( [ indexInventory, self.textName ] )
            inventory.append( [ idGDTaux, self.textName, P1, Direction, offsetValue ] )
        else:
            pass
        indexInventory+=1

        if hasattr(FreeCADGui,"Snapper") and idGDTaux != 1:
            if FreeCADGui.Snapper.grid:
                if FreeCADGui.Snapper.grid.Visible:
                    FreeCADGui.Snapper.grid.off()
                    FreeCADGui.Snapper.forceGridOff=True

        FreeCADGui.Control.closeDialog()

def getDefaultUnit(dim):
    '''return default Unit of Measure for a Dimension based on user preference
    Units Schema'''
    # only Length and Angle so far
    from FreeCAD import Units
    if dim == 'Length':
        qty = FreeCAD.Units.Quantity(1.0,FreeCAD.Units.Length)
        UOM = qty.getUserPreferred()[2]
    elif dim == 'Angle':
        qty = FreeCAD.Units.Quantity(1.0,FreeCAD.Units.Angle)
        UOM = qty.getUserPreferred()[2]
    else:
        UOM = "xx"
    return UOM

def makeFormatSpec(decimals=4,dim='Length'):
    ''' return a % format spec with specified decimals for a specified
    dimension based on on user preference Units Schema'''
    if dim == 'Length':
        fmtSpec = "%." + str(decimals) + "f "+ getDefaultUnit('Length')
    elif dim == 'Angle':
        fmtSpec = "%." + str(decimals) + "f "+ getDefaultUnit('Angle')
    else:
        fmtSpec = "%." + str(decimals) + "f " + "??"
    return fmtSpec

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

class fieldLabelWidget:
    def __init__(self, Text='Label'):
        self.Text = Text

    def generateWidget( self ):
        global offsetValue, Direction, P1
        Direction = FreeCADGui.Selection.getSelectionEx()[0].SubObjects[0].normalAt(0,0) # normalAt
        P1 = FreeCADGui.Selection.getSelectionEx()[0].SubObjects[0].CenterOfMass
        FreeCAD.DraftWorkingPlane.alignToPointAndAxis(P1, Direction, 0.0)
        FreeCADGui.Snapper.grid.set()
        self.FORMAT = makeFormatSpec(0,'Length')
        self.uiloader = FreeCADGui.UiLoader()
        self.inputfield = self.uiloader.createWidget("Gui::InputField")
        self.inputfield.setText(self.FORMAT % 0)
        offsetValue = 0
        QtCore.QObject.connect(self.inputfield,QtCore.SIGNAL("valueChanged(double)"),self.valueChanged)

        return GDTDialog_hbox(self.Text,self.inputfield)

    def valueChanged(self, d):
        global offsetValue, Direction, P1
        offsetValue = d
        FreeCAD.DraftWorkingPlane.alignToPointAndAxis(P1, Direction, offsetValue)
        FreeCADGui.Snapper.grid.set()

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
        elif self.Text == 'Active annotation plane:':
            self.k=5
        else:
            self.k=6

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
        global textDS, primary, secondary, tertiary, characteristic, datumSystem, combo, annotationPlane
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
        elif self.Text == 'Active annotation plane:':
            annotationPlane = self.List[combo[self.k].currentIndex()][0]
            FreeCAD.DraftWorkingPlane.alignToPointAndAxis(inventory[annotationPlane][2], inventory[annotationPlane][3], inventory[annotationPlane][4])
            FreeCADGui.Snapper.grid.set()

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

class fieldLabeCombolWidget:
    def __init__(self, Text='Label', List=[''], Icons=None, ToolTip = None):
        self.Text = Text
        self.List = List
        self.Icons = Icons
        self.ToolTip = ToolTip

    def generateWidget( self ):
        self.DECIMALS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Units").GetInt("Decimals",2)
        self.FORMAT = makeFormatSpec(self.DECIMALS,'Length')
        self.AFORMAT = makeFormatSpec(self.DECIMALS,'Angle')
        self.uiloader = FreeCADGui.UiLoader()
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
        self.inputfield = self.uiloader.createWidget("Gui::InputField")
        self.inputfield.setText(self.FORMAT % 0)
        global toleranceValue
        toleranceValue = 0
        QtCore.QObject.connect(self.inputfield,QtCore.SIGNAL("valueChanged(double)"),self.valueChanged)
        hbox.addLayout( GDTDialog_hbox(self.Text,self.inputfield) )
        hbox.addStretch(1)
        hbox.addWidget(self.combo)
        return hbox

    def updateDate(self):
        global featureControlFrame
        if self.ToolTip <> None:
            self.combo.setToolTip( self.ToolTip[self.combo.currentIndex()] )
        if self.Text == 'Tolerance value:':
            featureControlFrame = self.combo.currentIndex()

    def valueChanged(self,d):
        global toleranceValue
        toleranceValue = d

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

class helpGDTCommand:

    def Activated(self):
        QtGui.QMessageBox.information(
            QtGui.qApp.activeWindow(),
            'Geometric Dimensioning & Tolerancing Help',
            'Developing...' )
        #obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython","Annotation")
        #_Annotation(obj)

    def GetResources(self):
        return {
            'Pixmap' : ':/dd/icons/helpGDT.svg',
            'MenuText': 'Help',
            'ToolTip': 'Help'
            }

FreeCADGui.addCommand('dd_helpGDT', helpGDTCommand())
