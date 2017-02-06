# -*- coding: utf-8 -*-

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
    FreeCAD.Console.PrintMessage("FreeCAD Gui not present. GDT module will have some features disabled.")
    gui = False

try:
    from PySide import QtCore,QtGui,QtSvg
except ImportError:
    FreeCAD.Console.PrintMessage("Error: Python-pyside package must be installed on your system to use the Geometric Dimensioning & Tolerancing module.")

__dir__ = os.path.dirname(__file__)
iconPath = os.path.join( __dir__, 'Gui','Resources', 'icons' )
path_dd_resources =  os.path.join( os.path.dirname(__file__), 'Gui', 'Resources', 'dd_resources.rcc')
resourcesLoaded = QtCore.QResource.registerResource(path_dd_resources)
assert resourcesLoaded

textName = ''
textDS = ['','','']

primary = None
secondary = None
tertiary = None
characteristic = None
toleranceValue = 0.0
featureControlFrame = ''
datumSystem = 0
annotationPlane = 0
offsetValue = 0
P1 = FreeCAD.Vector(0.0,0.0,0.0)
Direction = FreeCAD.Vector(0.0,0.0,0.0)
sizeOfLine = 1.0

combo = ['','','','','','']
checkBoxState = True
auxDictionaryDS=[]
for i in range(1,100):
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

def getAllAnnotationObjects():
    "getAllAnnotationObjects(): returns a list of annotation objects"
    return getObjectsOfType("Annotation")

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
                Draft.setParam("gridEvery",getParam("gridEvery"))
                Draft.setParam("gridSpacing",getParam("gridSpacing"))
                Draft.setParam("gridSize",getParam("gridSize"))
                FreeCADGui.Snapper.grid.setMainlines(getParam("gridEvery"))
                FreeCADGui.Snapper.grid.setSpacing(getParam("gridSpacing"))
                FreeCADGui.Snapper.grid.setSize(getParam("gridSize"))
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

def saveCurrentFaceSelected():
    "saveCurrentFaceSelected(): returns a list of the last selected faces"
    Tuple = getSelectionEx()[0].SubObjects
    List = []
    for t in Tuple:
        List.append(t)
    return List

def createAnnotation(obj):
    doc = FreeCAD.ActiveDocument
    DF = obj.DF <> None
    if DF:
        Direction = obj.DF.Direction
        DirectionAP = obj.DF.AP.Direction
        PCenter = obj.DF.PCenter
        PointWithOffset = obj.DF.AP.PointWithOffset
        textName = obj.DF.Label
    else:
        Direction = obj.GT.Direction
        DirectionAP = obj.GT.AP.Direction
        PCenter = obj.GT.PCenter
        PointWithOffset = obj.GT.AP.PointWithOffset
        DECIMALS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Units").GetInt("Decimals",2)
        textName = displayExternal(obj.GT.ToleranceValue,DECIMALS,'Length',True)
        DS = 0
        if obj.GT.DS <> None:
            if obj.GT.DS.Primary <> None:
                DS+=1
            if obj.GT.DS.Secondary <> None:
                DS+=1
            if obj.GT.DS.Tertiary <> None:
                DS+=1

    def getPoint(point):
        if point:
            return plotLines(point)
        else:
            if DF:
                doc.removeObject(obj.DF.Name)
                if checkBoxState:
                    doc.removeObject(getAllDatumSystemObjects()[-1].Name)
            else:
                doc.removeObject(obj.GT.Name)
            doc.removeObject(obj.Name)
                #doc.removeObject(self.DS.Name)
            doc.recompute()

    def plotLines(point):
        d = point.distanceToPlane(PCenter,Direction)
        p1=PCenter.projectToPlane(PointWithOffset,DirectionAP)
        P2 = p1 + Direction * d
        P3 = point
        P4 = P3 + Direction * (-sizeOfLine)
        P5 = P3 + Direction * (sizeOfLine)
        pAux = P5 + DirectionAP * sizeOfLine
        v1 = pAux - P5
        v2 = P3 - P5
        Direction2 = v1.cross(v2)
        points = [p1,P2,P3,P4,P5]
        if DF:
            points += createDF(P5,Direction2)
        else:
            points += createGT(P5,Direction2)
        obj.Points = points
        myWire = Draft.makeWire(points,closed=False,face=True,support=None)
        myWire.ViewObject.LineColor = getRGBLine()
        myWire.ViewObject.LineWidth = getLineWidth()
        obj.WireConstruction = myWire
        if not DF:
            PText = points[-2] + Direction * (sizeOfLine/2)
            PText = PText + Direction2 * (sizeOfLine/2)
            PTextCharacteristic = points[3] + Direction * (sizeOfLine/2)
            PTextCharacteristic = PTextCharacteristic + Direction2 * (sizeOfLine)
            myLabel = Draft.makeText(obj.GT.CharacteristicIconText,point=PTextCharacteristic,screen=False)
            myLabel.ViewObject.FontSize = getTextSize()
            myLabel.ViewObject.FontName = getTextFamily()
            myLabel.ViewObject.TextColor = getRGBText()
            for i in range(DS):
                if i == 0:
                    PTextPrimary = points[-5] + Direction * (sizeOfLine/2)
                    PTextPrimary = PTextPrimary + Direction2 * (sizeOfLine/2)
                    myLabel = Draft.makeText(obj.GT.DS.Primary.Label,point=PTextPrimary,screen=False)
                    myLabel.ViewObject.FontSize = getTextSize()
                    myLabel.ViewObject.FontName = getTextFamily()
                    myLabel.ViewObject.TextColor = getRGBText()
                elif i == 1:
                    PTextSecondary = points[-8] + Direction * (sizeOfLine/2)
                    PTextSecondary = PTextSecondary + Direction2 * (sizeOfLine/2)
                    myLabel = Draft.makeText(obj.GT.DS.Secondary.Label,point=PTextSecondary,screen=False)
                    myLabel.ViewObject.FontSize = getTextSize()
                    myLabel.ViewObject.FontName = getTextFamily()
                    myLabel.ViewObject.TextColor = getRGBText()
                else:
                    PTextTertiary = points[-11] + Direction * (sizeOfLine/2)
                    PTextTertiary = PTextTertiary + Direction2 * (sizeOfLine/2)
                    myLabel = Draft.makeText(obj.GT.DS.Tertiary.Label,point=PTextTertiary,screen=False)
                    myLabel.ViewObject.FontSize = getTextSize()
                    myLabel.ViewObject.FontName = getTextFamily()
                    myLabel.ViewObject.TextColor = getRGBText()
        else:
            PText = points[-3] + Direction * (sizeOfLine/2)
            PText = PText + Direction2 * (sizeOfLine/2)
        myLabel = Draft.makeText(textName,point=PText,screen=False) # If screen is True, the text always faces the view direction.
        myLabel.ViewObject.FontSize = getTextSize()
        myLabel.ViewObject.FontName = getTextFamily()
        myLabel.ViewObject.TextColor = getRGBText()
        # grp = doc.addObject("Part::Compound","Annotation")
        # grp.Label='Annotation: '
        # grp.Links = [obj,myWire,myLabel,]
        FreeCAD.ActiveDocument.recompute()
        hideGrid()
        return obj

    def createDF(P5,Direction2):
        P6 = P5 + Direction2 * (sizeOfLine*3)
        P7 = P6 + Direction * (-sizeOfLine*2)
        P8 = P7 + Direction2 * (-sizeOfLine)
        P9 = P8 + Direction2 * (-sizeOfLine)
        P10 = P9 + Direction2 * (-sizeOfLine)
        P11=P9
        h=math.sqrt(sizeOfLine*sizeOfLine+(sizeOfLine/2)*(sizeOfLine/2))
        P12 = P11 + Direction2 * (sizeOfLine/2)
        P12 = P12 + Direction * (-h)
        P13=P8
        P14=P12

        P15 = P11 + Direction2 * (sizeOfLine/2)
        P15 = P15 + Direction * (-sizeOfLine*3)
        P16 = P15 + Direction2 * (sizeOfLine)
        P17 = P16 + Direction * (-sizeOfLine*2)
        P18 = P17 + Direction2 * (-sizeOfLine*2)
        P19 = P18 + Direction * (sizeOfLine*2)
        P20=P15
        return [P6,P7,P8,P9,P10,P11,P12,P13,P14,P15,P16,P17,P18,P19,P20]

    def createGT(P5,Direction2):
        listPoints=[]
        P6 = P5 + Direction2 * (sizeOfLine*11+sizeOfLine*DS*2)
        P7 = P6 + Direction * (-sizeOfLine*2)
        listPoints += [P6,P7]
        for i in range(DS):
            P8 = P7 + Direction2 * (-sizeOfLine*2)
            P9 = P8 + Direction * (sizeOfLine*2)
            P10 = P8
            P7 = P10
            listPoints += [P8,P9,P10]
        P8 = P7 + Direction2 * (-sizeOfLine*8)
        P9 = P8 + Direction * (sizeOfLine*2)
        P10 = P8
        P11 = P10 + Direction2 * (-sizeOfLine*3)
        #P11 = FreeCAD.Vector(P10[0]-sizeOfLine*3,P10[1],P10[2])
        listPoints += [P8,P9,P10,P11]
        return listPoints

    FreeCADGui.Snapper.getPoint(callback=getPoint)

def updateAnnotation(obj, objAnnotation):
    doc = FreeCAD.ActiveDocument
    posToInsert = 3
    DF = False
    if getType(obj) == "DatumFeature":
        DF = True
    if DF:
        DirectionAP = objAnnotation.GT.AP.Direction
        obj.AP = objAnnotation.GT.AP
        objAnnotation.DF = obj
        textName = obj.Label
    else:
        DirectionAP = objAnnotation.DF.AP.Direction
        obj.AP = objAnnotation.DF.AP
        objAnnotation.GT = obj
        DECIMALS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Units").GetInt("Decimals",2)
        textName = displayExternal(obj.ToleranceValue,DECIMALS,'Length',True)
        DS = 0
        posToInsert = len(objAnnotation.Points)-1
        if obj.DS <> None:
            if obj.DS.Primary <> None:
                DS+=1
            if obj.DS.Secondary <> None:
                DS+=1
            if obj.DS.Tertiary <> None:
                DS+=1
    Direction = obj.Direction
    DirectionAP = obj.AP.Direction
    p3 = objAnnotation.Points[2]
    p5 = objAnnotation.Points[4]
    pAux = p5 + DirectionAP * sizeOfLine
    v1 = pAux - p5
    v2 = p3 - p5
    Direction2 = v1.cross(v2)

    def updateDF(posToInsert, Direction, Direction2):
        List = objAnnotation.Points
        p1 = objAnnotation.Points[posToInsert]
        P2 = p1 + Direction2 * (sizeOfLine)
        h=math.sqrt(sizeOfLine*sizeOfLine+(sizeOfLine/2)*(sizeOfLine/2))
        P3 = P2 + Direction2 * (sizeOfLine/2)
        P3 = P3 + Direction * (-h)
        P4 = p1 + Direction2 * (sizeOfLine*2)
        P5 = P3
        P6 = P5 + Direction * (-sizeOfLine*3)
        P7 = P6 + Direction2 * (sizeOfLine)
        P8 = P7 + Direction * (-sizeOfLine*2)
        P9 = P8 + Direction2 * (-sizeOfLine*2)
        P10 = P9 + Direction * (sizeOfLine*2)
        P11 = P6
        P12 = P5
        P13 = P2
        P14 = p1
        pts = [p1,P2,P3,P4,P5,P6,P7,P8,P9,P10,P11,P12,P13,P14]
        for i in range(len(pts)):
            List.insert(posToInsert,pts[i])
            posToInsert+=1
        objAnnotation.Points = List
        doc.removeObject(objAnnotation.WireConstruction.Name)

    def updateGT(posToInsert, Direction, Direction2):
        p1 = objAnnotation.Points[posToInsert]

    if DF:
        updateDF(posToInsert, Direction, Direction2)
        points = objAnnotation.Points
        PText = points[11] + Direction2 * (sizeOfLine/2)
        PText = PText + Direction * (sizeOfLine/2)
    else:
        updateGT(posToInsert, Direction, Direction2)
        points = objAnnotation.Points

    myWire = Draft.makeWire(objAnnotation.Points,closed=False,face=False,support=None)
    myWire.ViewObject.LineColor = getRGBLine()
    myWire.ViewObject.LineWidth = getLineWidth()
    objAnnotation.WireConstruction = myWire
    myLabel = Draft.makeText(textName,point=PText,screen=False) # If screen is True, the text always faces the view direction.
    myLabel.ViewObject.FontSize = getTextSize()
    myLabel.ViewObject.FontName = getTextFamily()
    myLabel.ViewObject.TextColor = getRGBText()
    hideGrid()

def eqPlane(obj, target):
    if target == None:
        return False
    if len(obj) <> len(target):
        return False
    else:
        for i in range(len(obj)):
            if not obj[i].isEqual(target[i]):
                return False
    return True

def existPlane(obj):
    List = getObjectsOfType(["DatumFeature","GeometricTolerance"])
    count = 0
    for l in List:
        if eqPlane(obj,l.CurrentFaceSelected):
            count+=1
            if count > 1:
                return getAnnotation(l)
    return None

def existPlaneInDF(obj):
    List = getObjectsOfType(["DatumFeature"])
    count = 0
    for l in List:
        if eqPlane(obj,l.CurrentFaceSelected):
            return getAnnotation(l)
    return None

def existPlaneInGT(obj):
    List = getObjectsOfType(["GeometricTolerance"])
    count = 0
    for l in List:
        if eqPlane(obj,l.CurrentFaceSelected):
            return getAnnotation(l)
    return None

def getAnnotation(obj):
    List = getAllAnnotationObjects()
    for l in List:
        if l.DF == obj or l.GT == obj:
            return l
    return None

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
        '''Add some custom properties to our GDT feature'''
        obj.Proxy = self
        self.Type = tp

    def __getstate__(self):
        return self.Type

    def __setstate__(self,state):
        if state:
            self.Type = state

    def execute(self,obj):
        '''Do something when doing a recomputation, this method is mandatory'''
        pass

    def onChanged(self, obj, prop):
        '''Do something when a property has changed'''
        pass

class _ViewProviderGDT:
    "The base class for GDT Viewproviders"

    def __init__(self, vobj):
        '''Set this object to the proxy object of the actual view provider'''
        vobj.Proxy = self
        self.Object = vobj.Object

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    def attach(self,vobj):
        '''Setup the scene sub-graph of the view provider, this method is mandatory'''
        self.Object = vobj.Object
        return

    def updateData(self, obj, prop):
        '''If a property of the handled feature has changed we have the chance to handle this here'''
        # fp is the handled feature, prop is the name of the property that has changed
        return

    def getDisplayModes(self, vobj):
        '''Return a list of display modes.'''
        modes=[]
        return modes

    def setDisplayMode(self, mode):
        '''Map the display mode defined in attach with those defined in getDisplayModes.\
                Since they have the same names nothing needs to be done. This method is optional'''
        return mode

    def onChanged(self, vobj, prop):
        '''Here we can do something when a single property got changed'''
        return

    def execute(self,vobj):
        return

    def getIcon(self):
        '''Return the icon in XPM format which will appear in the tree view. This method is\
                optional and if not defined a default icon is shown.'''
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

def makeAnnotationPlane(Name, p1, Direction, Offset):
    ''' Explanation
    '''
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython","AnnotationPlane")
    _AnnotationPlane(obj)
    if gui:
        _ViewProviderAnnotationPlane(obj.ViewObject)
    obj.Label = Name
    obj.Point = p1
    obj.Direction = Direction
    obj.Offset = Offset
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
        obj.addProperty("App::PropertyVector","Direction","GDT","the axis direction of the face selected")
        obj.addProperty("App::PropertyVectorDistance","PCenter","GDT","mass center of the selected face")
        obj.addProperty("App::PropertyPythonObject","CurrentFaceSelected","","", 2)

    def onChanged(self,obj,prop):
        if hasattr(obj,"Direction"):
            obj.setEditorMode('Direction',2)
        if hasattr(obj,"PCenter"):
            obj.setEditorMode('PCenter',2)

    def execute(self,obj):
        '''Do something when doing a recomputation, this method is mandatory'''
        pass

class _ViewProviderDatumFeature(_ViewProviderGDT):
    "A View Provider for the GDT DatumFeature object"
    def __init__(self, obj):
        _ViewProviderGDT.__init__(self,obj)

    def updateData(self, obj, prop):
        "called when the base object is changed"
        if prop in ["AP","Direction","PCenter"]:
            pass


    def showAnnotationPlane(self):
        pass

    def getIcon(self):
        return(":/dd/icons/datumFeature.svg")

def makeDatumFeature(Name, AnnotationPlane, Direction, PCenter, CurrentFaceSelected):
    ''' Explanation
    '''
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython","DatumFeature")
    _DatumFeature(obj)
    if gui:
        _ViewProviderDatumFeature(obj.ViewObject)
    obj.Label = Name
    obj.AP = AnnotationPlane
    obj.Direction = Direction
    obj.PCenter = PCenter
    obj.CurrentFaceSelected = CurrentFaceSelected
    objAnnotation = existPlaneInGT(obj.CurrentFaceSelected)
    if objAnnotation <> None:
        updateAnnotation(obj, objAnnotation)
    else:
        makeAnnotation(Name="Annotation", DF=obj, CurrentFaceSelected=obj.CurrentFaceSelected)
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
        obj.addProperty("App::PropertyString","CharacteristicIcon","GDT","Characteristic of the geometric tolerance")
        obj.addProperty("App::PropertyString","CharacteristicIconText","GDT","Characteristic of the geometric tolerance")
        obj.addProperty("App::PropertyFloat","ToleranceValue","GDT","Tolerance value of the geometric tolerance")
        obj.addProperty("App::PropertyString","FeatureControlFrame","GDT","Feature control frame of the geometric tolerance")
        obj.addProperty("App::PropertyLink","DS","GDT","Datum system used")
        obj.addProperty("App::PropertyLink","AP","GDT","Annotation plane used")
        obj.addProperty("App::PropertyVector","Direction","GDT","the axis direction of the face selected")
        obj.addProperty("App::PropertyVectorDistance","PCenter","GDT","mass center of the selected face")
        obj.addProperty("App::PropertyPythonObject","CurrentFaceSelected","","",2)

    def onChanged(self,obj,prop):
        "Do something when a property has changed"
        if hasattr(obj,"CharacteristicIcon"):
            obj.setEditorMode('CharacteristicIcon',2)
        if hasattr(obj,"CharacteristicIconText"):
            obj.setEditorMode('CharacteristicIconText',2)

class _ViewProviderGeometricTolerance(_ViewProviderGDT):
    "A View Provider for the GDT GeometricTolerance object"
    def __init__(self, obj):
        _ViewProviderGDT.__init__(self,obj)

    def getIcon(self):
        icon = self.Object.CharacteristicIcon
        return icon

def makeGeometricTolerance(Name, Characteristic, CharacteristicIcon, CharacteristicIconText, ToleranceValue, FeatureControlFrame, DatumSystem, AnnotationPlane, Direction, PCenter, CurrentFaceSelected):
    ''' Explanation
    '''
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython","GeometricTolerance")
    _GeometricTolerance(obj)
    if gui:
        _ViewProviderGeometricTolerance(obj.ViewObject)
    obj.Label = Name
    obj.Characteristic = Characteristic
    obj.CharacteristicIcon = CharacteristicIcon
    obj.CharacteristicIconText = CharacteristicIconText
    obj.ToleranceValue = ToleranceValue
    obj.FeatureControlFrame = FeatureControlFrame
    obj.DS = DatumSystem
    obj.AP = AnnotationPlane
    obj.Direction = Direction
    obj.PCenter = PCenter
    obj.CurrentFaceSelected = CurrentFaceSelected
    objAnnotation = existPlaneInDF(obj.CurrentFaceSelected)
    if objAnnotation <> None:
        updateAnnotation(obj, objAnnotation)
    else:
        makeAnnotation(Name="Annotation", GT=obj, CurrentFaceSelected=obj.CurrentFaceSelected)
    FreeCAD.ActiveDocument.recompute()
    return obj

    #-----------------------------------------------------------------------
    # Annotation
    #-----------------------------------------------------------------------

class _Annotation(_GDTObject):
    "The GDT Annotation object"
    def __init__(self, obj):
        _GDTObject.__init__(self,obj,"Annotation")
        obj.addProperty("App::PropertyVectorList","Points","GDT","Points to make a wire")
        obj.addProperty("App::PropertyLink","DF","GDT","Text").DF=None
        obj.addProperty("App::PropertyLink","GT","GDT","Text").GT=None
        obj.addProperty("App::PropertyPythonObject","CurrentFaceSelected","","",2)
        obj.addProperty("App::PropertyLink","WireConstruction","","",2)

class _ViewProviderAnnotation(_ViewProviderGDT):
    "A View Provider for the GDT Annotation object"
    def __init__(self, obj):
        _ViewProviderGDT.__init__(self,obj)

    def getIcon(self):
        return(":/dd/icons/annotation.svg")

def makeAnnotation(Name, Points=[], DF=None, GT=None, CurrentFaceSelected=[]):
    ''' Explanation
    '''
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython","Annotation")
    _Annotation(obj)
    if gui:
        _ViewProviderAnnotation(obj.ViewObject)
    obj.Label = Name
    obj.Points = Points
    if DF <> None:
        obj.DF = DF
    if GT <> None:
        obj.GT = GT
    obj.CurrentFaceSelected = CurrentFaceSelected
    return createAnnotation(obj)

    #-----------------------------------------------------------------------
    # Other classes
    #-----------------------------------------------------------------------

class Characteristics(object):
    def __init__(self, Label, Icon, IconText):
        self.Label = Label
        self.Icon = Icon
        self.IconText = IconText
        self.Proxy = self

def makeCharacteristics(label):
    Label = ['Straightness', 'Flatness', 'Circularity', 'Cylindricity', 'Profile of a line', 'Profile of a surface', 'Perpendicularity', 'Angularity', 'Parallelism', 'Symmetry', 'Position', 'Concentricity','Circular run-out', 'Total run-out']
    Icon = [':/dd/icons/Characteristic/straightness.svg', ':/dd/icons/Characteristic/flatness.svg', ':/dd/icons/Characteristic/circularity.svg', ':/dd/icons/Characteristic/cylindricity.svg', ':/dd/icons/Characteristic/profileOfALine.svg', ':/dd/icons/Characteristic/profileOfASurface.svg', ':/dd/icons/Characteristic/perpendicularity.svg', ':/dd/icons/Characteristic/angularity.svg', ':/dd/icons/Characteristic/parallelism.svg', ':/dd/icons/Characteristic/symmetry.svg', ':/dd/icons/Characteristic/position.svg', ':/dd/icons/Characteristic/concentricity.svg',':/dd/icons/Characteristic/circularRunOut.svg', ':/dd/icons/Characteristic/totalRunOut.svg']
    textIcon = [('⏤').decode('utf-8'),('⏥').decode('utf-8'),('○').decode('utf-8'),('⌭').decode('utf-8'),('⌒').decode('utf-8'),('⌓').decode('utf-8'),('⟂').decode('utf-8'),('∠').decode('utf-8'),('∥').decode('utf-8'),('⌯').decode('utf-8'),('⌖').decode('utf-8'),('◎').decode('utf-8'),('↗').decode('utf-8'),('⌰').decode('utf-8')]
    index = Label.index(label)
    icon = Icon[index]
    iconText = textIcon[index]
    characteristics = Characteristics(label, icon, iconText)
    return characteristics

class FeatureControlFrame(object):
    def __init__(self, Label, Icon, toolTip):
        self.Label = Label
        self.Icon = Icon
        self.toolTip = toolTip
        self.Proxy = self

def makeFeatureControlFrame():
    Label = ['','','','','','','','']
    Icon = ['', ':/dd/icons/FeatureControlFrame/freeState.svg', ':/dd/icons/FeatureControlFrame/leastMaterialCondition.svg', ':/dd/icons/FeatureControlFrame/maximumMaterialCondition.svg', ':/dd/icons/FeatureControlFrame/projectedToleranceZone.svg', ':/dd/icons/FeatureControlFrame/regardlessOfFeatureSize.svg', ':/dd/icons/FeatureControlFrame/tangentPlane.svg', ':/dd/icons/FeatureControlFrame/unequalBilateral.svg']
    toolTip = ['Feature control frame', 'Free state', 'Least material condition', 'Maximum material condition', 'Projected tolerance zone', 'Regardless of feature size', 'Tangent plane', 'Unequal Bilateral']
    featureControlFrame = FeatureControlFrame(Label, Icon, toolTip)
    return featureControlFrame

#---------------------------------------------------------------------------
# Customized widgets
#---------------------------------------------------------------------------

class GDTWidget:
    def __init__(self):
        self.dialogWidgets = []
        self.CurrentFaceSelected = []

    def activate( self, idGDT=0, dialogTitle='GD&T Widget', dialogIconPath=':/dd/icons/GDT.svg', endFunction=None, dictionary=None):
        self.dialogTitle=dialogTitle
        self.dialogIconPath = dialogIconPath
        self.endFunction = endFunction
        self.dictionary = dictionary
        self.idGDT=idGDT
        if self.idGDT in [1,3,4]:
            self.CurrentFaceSelected = saveCurrentFaceSelected()
        global combo
        combo = ['','','','','','']
        extraWidgets = []
        if dictionary <> None:
            extraWidgets.append(textLabelWidget(Text='Name:',Mask='NNNn', Dictionary=self.dictionary)) #http://doc.qt.io/qt-5/qlineedit.html#inputMask-prop
        else:
            extraWidgets.append(textLabelWidget(Text='Name:',Mask='NNNn'))
        self.taskDialog = GDTDialog( self.dialogTitle, self.dialogIconPath, self.idGDT, extraWidgets + self.dialogWidgets, self.CurrentFaceSelected)
        FreeCADGui.Control.showDialog( self.taskDialog )

class GDTDialog:
    def __init__(self, title, iconPath, idGDT, dialogWidgets, CurrentFaceSelected):
        self.initArgs = title, iconPath, idGDT, dialogWidgets, CurrentFaceSelected
        self.createForm()

    def createForm(self):
        title, iconPath, idGDT, dialogWidgets, CurrentFaceSelected = self.initArgs
        self.form = GDTGuiClass( title, idGDT, dialogWidgets, CurrentFaceSelected)
        self.form.setWindowTitle( title )
        self.form.setWindowIcon( QtGui.QIcon( iconPath ) )

    def reject(self): #close button
        hideGrid()
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.Control.closeDialog()

    def getStandardButtons(self): #http://forum.freecadweb.org/viewtopic.php?f=10&t=11801
        return 0x00200000 #close button

class GDTGuiClass(QtGui.QWidget):

    def __init__(self, title, idGDT, dialogWidgets, CurrentFaceSelected):
        super(GDTGuiClass, self).__init__()
        self.dd_dialogWidgets = dialogWidgets
        self.title = title
        self.idGDT = idGDT
        self.CurrentFaceSelected = CurrentFaceSelected
        self.initUI( self.title , self.idGDT, self.CurrentFaceSelected)

    def initUI(self, title, idGDT, CurrentFaceSelected):
        self.idGDT = idGDT
        self.CurrentFaceSelected = CurrentFaceSelected
        vbox = QtGui.QVBoxLayout()
        for widg in self.dd_dialogWidgets:
            w = widg.generateWidget(self.idGDT)
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
        global textName, textDS, primary, secondary, tertiary, characteristic, toleranceValue, featureControlFrame, datumSystem, annotationPlane, auxDictionaryDS, P1, Direction, offsetValue
        self.textName = textName.encode('utf-8')
        if self.idGDT == 1:
            Direction = self.CurrentFaceSelected[0].Surface.Axis # to Axis    .normalAt(0,0) # normalAt
            PCenter = self.CurrentFaceSelected[0].CenterOfMass
            obj = makeDatumFeature(self.textName, annotationPlane, Direction, PCenter, self.CurrentFaceSelected)
            if checkBoxState:
                self.DS = makeDatumSystem(auxDictionaryDS[len(getAllDatumSystemObjects())] + ': ' + self.textName, obj, None, None)
            # createGDT(self,obj)
        elif self.idGDT == 2:
            separator = ' | '
            if textDS[0] <> '':
                if textDS[1] <> '':
                    if textDS[2] <> '':
                        self.textName = self.textName + ': ' + separator.join(textDS)
                    else:
                        self.textName = self.textName + ': ' + separator.join([textDS[0], textDS[1]])
                else:
                    self.textName = self.textName + ': ' + textDS[0]
            else:
                self.textName = self.textName
            makeDatumSystem(self.textName, primary, secondary, tertiary)
        elif self.idGDT == 3:
            Direction = self.CurrentFaceSelected[0].Surface.Axis # to Axis    .normalAt(0,0) # normalAt
            PCenter = self.CurrentFaceSelected[0].CenterOfMass
            makeGeometricTolerance(self.textName, characteristic.Label, characteristic.Icon, characteristic.IconText, toleranceValue, featureControlFrame, datumSystem, annotationPlane, Direction, PCenter, self.CurrentFaceSelected)
        elif self.idGDT == 4:
            makeAnnotationPlane(self.textName, P1, Direction, offsetValue)
        else:
            pass

        if self.idGDT != 1 and self.idGDT != 3:
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
    def __init__(self, Text='Label', Mask=None, Dictionary=None):
        self.Text = Text
        self.Mask = Mask
        self.Dictionary = Dictionary

    def generateWidget( self, idGDT ):
        self.idGDT = idGDT
        self.lineEdit = QtGui.QLineEdit()
        if self.Mask <> None:
            self.lineEdit.setInputMask(self.Mask)
        if self.Dictionary == None:
            self.lineEdit.setText('text')
            self.text = 'text'
        else:
            NumberOfObjects = self.getNumberOfObjects()
            if NumberOfObjects > len(self.Dictionary)-1:
                NumberOfObjects = len(self.Dictionary)-1
            self.lineEdit.setText(self.Dictionary[NumberOfObjects])
            self.text = self.Dictionary[NumberOfObjects]
        self.lineEdit.textChanged.connect(self.valueChanged)
        global textName
        textName = self.text.strip()
        return GDTDialog_hbox(self.Text,self.lineEdit)

    def valueChanged(self, argGDT):
        self.text = argGDT.strip()
        global textName
        textName = self.text

    def getNumberOfObjects(self):
        "getNumberOfObjects(): returns the number of objects of the same type as the active widget"
        if self.idGDT == 1:
            NumberOfObjects = len(getAllDatumFeatureObjects())
        elif self.idGDT == 2:
            NumberOfObjects = len(getAllDatumSystemObjects())
        elif self.idGDT == 3:
            NumberOfObjects = len(getAllGeometricToleranceObjects())
        elif self.idGDT == 4:
            NumberOfObjects = len(getAllAnnotationPlaneObjects())
        else:
            NumberOfObjects = 0
        return NumberOfObjects

class fieldLabelWidget:
    def __init__(self, Text='Label'):
        self.Text = Text

    def generateWidget( self, idGDT ):
        self.idGDT = idGDT
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
    def __init__(self, Text='Label', List=None, Icons=None, ToolTip = None):
        self.Text = Text
        self.List = List
        self.Icons = Icons
        self.ToolTip = ToolTip

    def generateWidget( self, idGDT ):
        self.idGDT = idGDT
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
                combo[self.k].addItem( QtGui.QIcon(self.Icons[i]), self.List[i] )
            else:
                if self.List[i] == None:
                    combo[self.k].addItem( '' )
                else:
                    combo[self.k].addItem( self.List[i].Label )
        if self.Text == 'Secondary:' or self.Text == 'Tertiary:':
            combo[self.k].setEnabled(False)
        if self.ToolTip <> None:
            combo[self.k].setToolTip( self.ToolTip[0] )
        self.comboIndex = combo[self.k].currentIndex()
        if self.k <> 0 and self.k <> 1:
            self.updateDate(self.comboIndex)
        combo[self.k].activated.connect(lambda comboIndex = self.comboIndex: self.updateDate(comboIndex))
        return GDTDialog_hbox(self.Text,combo[self.k])

    def updateDate(self, comboIndex):
        global textDS, primary, secondary, tertiary, characteristic, datumSystem, combo, annotationPlane
        if self.ToolTip <> None:
            combo[self.k].setToolTip( self.ToolTip[comboIndex] )
        if self.Text == 'Primary:':
            textDS[0] = combo[self.k].currentText()
            primary = self.List[comboIndex]
            if comboIndex <> 0:
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
            secondary = self.List[comboIndex]
            if comboIndex <> 0:
                combo[2].setEnabled(True)
            else:
                combo[2].setEnabled(False)
                combo[2].setCurrentIndex(0)
                textDS[2] = ''
                tertiary = None
            self.updateItemsEnabled(self.k)
        elif self.Text == 'Tertiary:':
            textDS[2] = combo[self.k].currentText()
            tertiary = self.List[comboIndex]
            self.updateItemsEnabled(self.k)
        elif self.Text == 'Characteristic:':
            characteristic = makeCharacteristics(self.List[comboIndex])
        elif self.Text == 'Datum system:':
            datumSystem = self.List[comboIndex]
        elif self.Text == 'Active annotation plane:':
            annotationPlane = self.List[comboIndex]
            Direction = self.List[comboIndex].Direction
            PointWithOffset = self.List[comboIndex].PointWithOffset
            FreeCAD.DraftWorkingPlane.alignToPointAndAxis(PointWithOffset, Direction, 0.0)
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

    def generateWidget( self, idGDT ):
        self.idGDT = idGDT
        self.group = QtGui.QGroupBox(self.Text)
        vbox = QtGui.QVBoxLayout()
        for l in self.List:
            vbox.addLayout(l.generateWidget(self.idGDT))
        self.group.setLayout(vbox)
        return self.group

class fieldLabeCombolWidget:
    def __init__(self, Text='Label', List=[''], Icons=None, ToolTip = None):
        self.Text = Text
        self.List = List
        self.Icons = Icons
        self.ToolTip = ToolTip

    def generateWidget( self, idGDT ):
        self.idGDT = idGDT
        self.DECIMALS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Units").GetInt("Decimals",2)
        self.FORMAT = makeFormatSpec(self.DECIMALS,'Length')
        self.AFORMAT = makeFormatSpec(self.DECIMALS,'Angle')
        self.uiloader = FreeCADGui.UiLoader()
        self.combo = QtGui.QComboBox()
        global featureControlFrame, toleranceValue
        for i in range(len(self.List)):
            if self.Icons <> None:
                self.combo.addItem( QtGui.QIcon(self.Icons[i]), self.List[i] )
            else:
                self.combo.addItem( self.List[i] )
        if self.ToolTip <> None:
           self.updateDate()
        self.combo.activated.connect(self.updateDate)
        hbox = QtGui.QHBoxLayout()
        self.inputfield = self.uiloader.createWidget("Gui::InputField")
        self.inputfield.setText(self.FORMAT % 0)
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
            if self.combo.currentIndex() <> 0:
                featureControlFrame = self.ToolTip[self.combo.currentIndex()]
            else:
                featureControlFrame = ''

    def valueChanged(self,d):
        global toleranceValue
        toleranceValue = d

class CheckBoxWidget:
    def __init__(self, Text='Label'):
        self.Text = Text

    def generateWidget( self, idGDT ):
        self.idGDT = idGDT
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
