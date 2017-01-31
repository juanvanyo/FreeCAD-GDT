
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

#---------------------------------------------------------------------------
# Param functions
#---------------------------------------------------------------------------

def getParamType(param):
    if param in ["lineWidth","gridEvery","gridSize"]:
        return "int"
    elif param in ["textFamily"]:
        return "string"
    elif param in ["textSize","gridSpacing"]:
        return "float"
    elif param in ["alwaysShowGrid"]:
        return "bool"
    elif param in ["textColor","lineColor"]:
        return "unsigned"
    else:
        return None

def getParam(param,default=None):
    "getParam(parameterName): returns a GDT parameter value from the current config"
    p = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/GDT")
    t = getParamType(param)
    if t == "int":
        if default == None:
            default = 0
        return p.GetInt(param,default)
    elif t == "string":
        if default == None:
            default = ""
        return p.GetString(param,default)
    elif t == "float":
        if default == None:
            default = 1
        return p.GetFloat(param,default)
    elif t == "bool":
        if default == None:
            default = False
        return p.GetBool(param,default)
    elif t == "unsigned":
        if default == None:
            default = 0
        return p.GetUnsigned(param,default)
    else:
        return None

def setParam(param,value):
    "setParam(parameterName,value): sets a GDT parameter with the given value"
    p = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/GDT")
    t = getParamType(param)
    if t == "int": p.SetInt(param,value)
    elif t == "string": p.SetString(param,value)
    elif t == "float": p.SetFloat(param,value)
    elif t == "bool": p.SetBool(param,value)
    elif t == "unsigned": p.SetUnsigned(param,value)

#---------------------------------------------------------------------------
# General functions
#---------------------------------------------------------------------------

def getRealName(name):
    "getRealName(string): strips the trailing numbers from a string name"
    for i in range(1,len(name)):
        if not name[-i] in '1234567890':
            return name[:len(name)-(i-1)]
    return name

def getType(obj):
    "getType(object): returns the GDT type of the given object"
    if not obj:
        return None
    if "Proxy" in obj.PropertiesList:
        if hasattr(obj.Proxy,"Type"):
            return obj.Proxy.Type
    return "Unknown"

def getObjectsOfType(typeList):
    "getObjectsOfType(string): returns a list of objects of the given type"
    listObjectsOfType = []
    objs = FreeCAD.ActiveDocument.Objects
    if not isinstance(typeList,list):
        typeList = [typeList]
    for obj in objs:
        for typ in typeList:
            if typ == getType(obj):
                listObjectsOfType.append(obj)
    return listObjectsOfType

def getAllAnnotationPlaneObjects():
    "getAllAnnotationPlaneObjects(): returns a list of annotation plane objects"
    return getObjectsOfType("AnnotationPlane")

def getAllDatumFeatureObjects():
    "getAllDatumFeatureObjects(): returns a list of datum feature objects"
    return getObjectsOfType("DatumFeature")

def getAllDatumSystemObjects():
    "getAllDatumSystemObjects(): returns a list of datum system objects"
    return getObjectsOfType("DatumSystem")

def getAllGeometricToleranceObjects():
    "getAllGeometricToleranceObjects(): returns a list of geometric tolerance objects"
    return getObjectsOfType("GeometricTolerance")

def getAllGDTObjects():
    "getAllGDTObjects(): returns a list of GDT objects"
    return getObjectsOfType(["AnnotationPlane","DatumFeature","DatumSystem","GeometricTolerance"])

def getRGB(param):
    color = QtGui.QColor(getParam(param,16753920)>>8)
    r = float(color.red()/255.0)
    g = float(color.green()/255.0)
    b = float(color.blue()/255.0)
    col = (r,g,b,0.0)
    return col

def getRGBText():
    return getRGB("textColor")

def getTextFamily():
    return getParam("textFamily","")

def getTextSize():
    return getParam("textSize",2.2)

def getLineWidth():
    return getParam("lineWidth",2)

def getRGBLine():
    return getRGB("lineColor")

def hideGrid():
    if hasattr(FreeCADGui,"Snapper") and getParam("alwaysShowGrid") == False:
        if FreeCADGui.Snapper.grid:
            if FreeCADGui.Snapper.grid.Visible:
                FreeCADGui.Snapper.grid.off()
                FreeCADGui.Snapper.forceGridOff=True

def showGrid():
    if hasattr(FreeCADGui,"Snapper"):
        if FreeCADGui.Snapper.grid:
            if FreeCADGui.Snapper.grid.Visible == False:
                FreeCADGui.Snapper.grid.reset()
                FreeCADGui.Snapper.grid.on()
                FreeCADGui.Snapper.forceGridOff=False
        else:
            FreeCADGui.Snapper.show()

def getSelection():
    "getSelection(): returns the current FreeCAD selection"
    if gui:
        return FreeCADGui.Selection.getSelection()
    return None

def getSelectionEx():
    "getSelectionEx(): returns the current FreeCAD selection (with subobjects)"
    if gui:
        return FreeCADGui.Selection.getSelectionEx()
    return None

def select(objs=None):
    "select(object): deselects everything and selects only the passed object or list"
    if gui:
        FreeCADGui.Selection.clearSelection()
        if objs:
            if not isinstance(objs,list):
                objs = [objs]
            for obj in objs:
                FreeCADGui.Selection.addSelection(obj)

#---------------------------------------------------------------------------
# UNITS handling
#---------------------------------------------------------------------------

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

def displayExternal(internValue,decimals=4,dim='Length',showUnit=True):
    '''return an internal value (ie mm) Length or Angle converted for display according
    to Units Schema in use.'''
    from FreeCAD import Units

    if dim == 'Length':
        qty = FreeCAD.Units.Quantity(internValue,FreeCAD.Units.Length)
        pref = qty.getUserPreferred()
        conversion = pref[1]
        uom = pref[2]
    elif dim == 'Angle':
        qty = FreeCAD.Units.Quantity(internValue,FreeCAD.Units.Angle)
        pref=qty.getUserPreferred()
        conversion = pref[1]
        uom = pref[2]
    else:
        conversion = 1.0
        uom = "??"
    if not showUnit:
        uom = ""
    fmt = "{0:."+ str(decimals) + "f} "+ uom
    displayExt = fmt.format(float(internValue) / float(conversion))
    displayExt = displayExt.replace(".",QtCore.QLocale().decimalPoint())
    return displayExt

#---------------------------------------------------------------------------
# Python Features definitions
#---------------------------------------------------------------------------

    #-----------------------------------------------------------------------
    # Base class for GDT objects
    #-----------------------------------------------------------------------

class _GDTObject:
    "The base class for GDT objects"
    def __init__(self,obj,tp="Unknown"):
        obj.Proxy = self
        self.Type = tp

    def __getstate__(self):
        return self.Type

    def __setstate__(self,state):
        if state:
            self.Type = state

    def execute(self,obj):
        pass

    def onChanged(self, obj, prop):
        pass

class _ViewProviderGDT:
    "The base class for GDT Viewproviders"

    def __init__(self, vobj):
        vobj.Proxy = self
        self.Object = vobj.Object

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    def attach(self,vobj):
        self.Object = vobj.Object
        return

    def updateData(self, obj, prop):
        "called when the base object is changed"
        return

    def getDisplayModes(self, vobj):
        modes=[]
        return modes

    def setDisplayMode(self, mode):
        return mode

    def onChanged(self, vobj, prop):
        "called when a view property has changed"
        return

    def execute(self,vobj):
        return

    def getIcon(self):
        return(":/dd/icons/GDT.svg")

    #-----------------------------------------------------------------------
    # Annotation Plane
    #-----------------------------------------------------------------------

class _AnnotationPlane(_GDTObject):
    "The GDT AnnotationPlane object"
    def __init__(self, obj):
        _GDTObject.__init__(self,obj,"AnnotationPlane")
        obj.addProperty("App::PropertyVectorDistance","Point","GDT","Center point of Grid")
        obj.addProperty("App::PropertyVectorDistance","PointWithOffset","GDT","Center point of Grid with offset applied")
        obj.addProperty("App::PropertyVector","Direction","GDT","The normal direction of this annotation plane")
        obj.addProperty("App::PropertyFloat","Offset","GDT","The offset value to aply in this annotation plane")

    def onChanged(self,obj,prop):
        if hasattr(obj,"PointWithOffset"):
            obj.setEditorMode('PointWithOffset',1)

class _ViewProviderAnnotationPlane(_ViewProviderGDT):
    "A View Provider for the GDT AnnotationPlane object"
    def __init__(self, obj):
        _ViewProviderGDT.__init__(self,obj)

    def updateData(self, obj, prop):
        "called when the base object is changed"
        if prop in ["Point","Direction","Offset"]:
            obj.PointWithOffset = obj.Point + obj.Direction*obj.Offset

    def getIcon(self):
        return(":/dd/icons/annotationPlane.svg")

def makeAnnotationPlane(Name, P1, Direction, Offset):
    ''' Explanation
    '''
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython","AnnotationPlane")
    _AnnotationPlane(obj)
    if gui:
        _ViewProviderAnnotationPlane(obj.ViewObject)
    obj.Label = Name
    obj.Point = P1
    obj.Direction = Direction
    obj.Offset = Offset
    obj.PointWithOffset = P1 + Direction*Offset
    FreeCAD.ActiveDocument.recompute()
    return obj

    #-----------------------------------------------------------------------
    # Datum Feature
    #-----------------------------------------------------------------------

class _DatumFeature(_GDTObject):
    "The GDT DatumFeature object"
    def __init__(self, obj):
        _GDTObject.__init__(self,obj,"DatumFeature")
        obj.addProperty("App::PropertyLink","AP","GDT","Annotation plane used")

class _ViewProviderDatumFeature(_ViewProviderGDT):
    "A View Provider for the GDT DatumFeature object"
    def __init__(self, obj):
        _ViewProviderGDT.__init__(self,obj)

    def showAnnotationPlane(self):
        pass

    def getIcon(self):
        return(":/dd/icons/datumFeature.svg")

def makeDatumFeature(Name, AnnotationPlane):
    ''' Explanation
    '''
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython","DatumFeature")
    _DatumFeature(obj)
    if gui:
        _ViewProviderDatumFeature(obj.ViewObject)
    obj.Label = Name
    obj.AP = AnnotationPlane
    FreeCAD.ActiveDocument.recompute()
    return obj

    #-----------------------------------------------------------------------
    # Datum System
    #-----------------------------------------------------------------------

class _DatumSystem(_GDTObject):
    "The GDT DatumSystem object"
    def __init__(self, obj):
        _GDTObject.__init__(self,obj,"DatumSystem")
        obj.addProperty("App::PropertyLink","Primary","GDT","Primary datum feature used")
        obj.addProperty("App::PropertyLink","Secondary","GDT","Secondary datum feature used")
        obj.addProperty("App::PropertyLink","Tertiary","GDT","Tertiary datum feature used")

class _ViewProviderDatumSystem(_ViewProviderGDT):
    "A View Provider for the GDT DatumSystem object"
    def __init__(self, obj):
        _ViewProviderGDT.__init__(self,obj)

    def getIcon(self):
        return(":/dd/icons/datumSystem.svg")

def makeDatumSystem(Name, Primary, Secondary=None, Tertiary=None):
    ''' Explanation
    '''
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython","DatumSystem")
    _DatumSystem(obj)
    if gui:
        _ViewProviderDatumSystem(obj.ViewObject)
    obj.Label = Name
    obj.Primary = Primary
    obj.Secondary = Secondary
    obj.Tertiary = Tertiary
    FreeCAD.ActiveDocument.recompute()
    return obj

    #-----------------------------------------------------------------------
    # Geometric Tolerance
    #-----------------------------------------------------------------------

class _GeometricTolerance(_GDTObject):
    "The GDT GeometricTolerance object"
    def __init__(self, obj):
        _GDTObject.__init__(self,obj,"GeometricTolerance")
        obj.addProperty("App::PropertyString","Characteristic","GDT","Characteristic of the geometric tolerance")
        obj.addProperty("App::PropertyFloat","ToleranceValue","GDT","Tolerance value of the geometric tolerance")
        obj.addProperty("App::PropertyFloat","FeatureControlFrame","GDT","Feature control frame of the geometric tolerance")
        obj.addProperty("App::PropertyLink","DS","GDT","Datum system used")
        obj.addProperty("App::PropertyLink","AP","GDT","Annotation plane used")

class _ViewProviderGeometricTolerance(_ViewProviderGDT):
    "A View Provider for the GDT GeometricTolerance object"
    def __init__(self, obj):
        _ViewProviderGDT.__init__(self,obj)

    def getIcon(self):
        return(":/dd/icons/geometricTolerance.svg")

def makeGeometricTolerance(Name, Characteristic, ToleranceValue, FeatureControlFrame, DatumSystem, AnnotationPlane):
    ''' Explanation
    '''
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython","GeometricTolerance")
    _GeometricTolerance(obj)
    if gui:
        _ViewProviderGeometricTolerance(obj.ViewObject)
    obj.Label = Name
    obj.Characteristic = Characteristic
    obj.ToleranceValue = ToleranceValue
    obj.FeatureControlFrame = FeatureControlFrame
    obj.DS = DatumSystem
    obj.AP = AnnotationPlane
    FreeCAD.ActiveDocument.recompute()
    return obj

#---------------------------------------------------------------------------
# Customized widgets
#---------------------------------------------------------------------------

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
        hideGrid()
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
        buttonCreate.clicked.connect(self.createObject)
        hbox.addStretch(1)
        hbox.addWidget( buttonCreate )
        hbox.addStretch(1)
        vbox.addLayout( hbox )
        self.setLayout(vbox)

    def createObject(self):
        global indexGDT, indexDF, indexDS, indexGT, indexAP, idGDTaux, textName, textGDT, listDF, listDS, listGT, listAP, textDS, inventory, indexInventory, primary, secondary, tertiary, characteristic, toleranceValue, featureControlFrame, datumSystem, annotationPlane, auxDictionaryDS, P1, Direction, offsetValue
        self.textName = textName.encode('utf-8')
        self.view = Draft.get3DView()
        self.point = FreeCAD.Vector(0.0,0.0,0.0)

        def cb(point):
            if point:
                self.point = point
                # FreeCAD.Console.PrintMessage('Punto seleccionado: ' + str(self.point) + '\n')
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
            myWire.ViewObject.LineColor = getRGBLine()
            myWire.ViewObject.LineWidth = getLineWidth()
            myLabel = Draft.makeText(self.textName,point=PText,screen=False) # If screen is True, the text always faces the view direction.
            myLabel.ViewObject.FontSize = getTextSize()
            myLabel.ViewObject.FontName = getTextFamily()
            myLabel.ViewObject.TextColor = getRGBText()
            # FreeCAD.Console.PrintMessage('Direction: ' + str(Direction) + '\n')
            # FreeCAD.Console.PrintMessage('P1: ' + str(P1) + '\n')
            # FreeCAD.Console.PrintMessage('P2: ' + str(P2) + '\n')
            # FreeCAD.Console.PrintMessage('P3: ' + str(P3) + '\n')
            # FreeCAD.Console.PrintMessage('P4: ' + str(P4) + '\n')
            hideGrid()

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
            # Direction = getSelectionEx()[0].SubObjects[0].normalAt(0,0) # normalAt
            Direction = getSelectionEx()[0].SubObjects[0].Surface.Axis # to Axis    .normalAt(0,0) # normalAt
            PCenter = getSelectionEx()[0].SubObjects[0].CenterOfMass
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
            makeDatumFeature(self.textName,getAllAnnotationPlaneObjects()[0])


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
            makeAnnotationPlane(self.textName, P1, Direction, offsetValue)
        else:
            pass
        indexInventory+=1

        if idGDTaux != 1:
            hideGrid()

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

class fieldLabelWidget:
    def __init__(self, Text='Label'):
        self.Text = Text

    def generateWidget( self ):
        global offsetValue, Direction, P1
        Direction = getSelectionEx()[0].SubObjects[0].normalAt(0,0) # normalAt
        P1 = getSelectionEx()[0].SubObjects[0].CenterOfMass
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
