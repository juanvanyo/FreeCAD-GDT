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
from math import pi
from FreeCAD import Vector
from svgLib_dd import SvgTextRenderer, SvgTextParser
import traceback
import Draft
import Part
from pivy import coin
import FreeCADGui, WorkingPlane
if FreeCAD.GuiUp:
    gui = True
else:
    FreeCAD.Console.PrintMessage("FreeCAD Gui not present. GDT module will have some features disabled.")
    gui = True

try:
    from PySide import QtCore,QtGui,QtSvg
except ImportError:
    FreeCAD.Console.PrintMessage("Error: Python-pyside package must be installed on your system to use the Geometric Dimensioning & Tolerancing module.")

__dir__ = os.path.dirname(__file__)
iconPath = os.path.join( __dir__, 'Gui','Resources', 'icons' )
path_dd_resources =  os.path.join( os.path.dirname(__file__), 'Gui', 'Resources', 'dd_resources.rcc')
resourcesLoaded = QtCore.QResource.registerResource(path_dd_resources)
assert resourcesLoaded

checkBoxState = True
auxDictionaryDS=[]
for i in range(1,100):
    auxDictionaryDS.append('DS'+str(i))
dictionaryAnnotation=[]
for i in range(1,100):
    dictionaryAnnotation.append('Annotation'+str(i))

#---------------------------------------------------------------------------
# Param functions
#---------------------------------------------------------------------------

def getParamType(param):
    if param in ["lineWidth","gridEvery","gridSize"]:
        return "int"
    elif param in ["textFamily"]:
        return "string"
    elif param in ["textSize","gridSpacing","lineScale"]:
        return "float"
    elif param in ["alwaysShowGrid","showUnit"]:
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

def select(obj):
    "select(object): deselects everything and selects only the working faces of the passed object"
    if gui:
        FreeCADGui.Selection.clearSelection()
        for i in range(len(obj.faces)):
            FreeCADGui.Selection.addSelection(obj.faces[i][0],obj.faces[i][1])

def makeContainerOfData():
    ""
    faces = []
    for i in range(len(getSelectionEx())):
        for j in range(len(getSelectionEx()[i].SubElementNames)):
            faces.append((getSelectionEx()[i].Object, getSelectionEx()[i].SubElementNames[j]))
    faces.sort()
    container = ContainerOfData(faces)
    return container

def getAnnotationObj(obj):
    List = getAllAnnotationObjects()
    for l in List:
        if l.faces == obj.faces:
            return l
    return None

def getAnnotationWithDF(obj):
    List = getAllAnnotationObjects()
    for l in List:
        if l.DF == obj:
            return l
    return None

def getAnnotationWithGT(obj):
    List = getAllAnnotationObjects()
    for l in List:
        for gt in l.GT:
            if gt == obj:
                return l
    return None

def getPointsToPlot(obj):
    X = FreeCAD.Vector(1.0,0.0,0.0)
    Y = FreeCAD.Vector(0.0,1.0,0.0)
    Direction = X if abs(X.dot(obj.AP.Direction)) < 0.8 else Y
    Vertical = obj.AP.Direction.cross(Direction).normalize()
    Horizontal = Vertical.cross(obj.AP.Direction).normalize()
    point = obj.selectedPoint
    d = point.distanceToPlane(obj.p1, obj.Direction)
    if obj.circumferenceBool:
        P3 = point + obj.Direction * (-d)
        d2 = (P3 - obj.p1) * Vertical
        P2 = obj.p1 + Vertical * (d2*3/4)
    else:
        P2 = obj.p1 + obj.Direction * (d*3/4)
        P3 = point
    points = [obj.p1, P2, P3]
    segments = [0,1,2]
    existGT = True
    if obj.GT <> []:
        points, segments = getPointsToPlotGT(obj, points, segments, Vertical, Horizontal)
    else:
        existGT = False
    if obj.DF <> None:
        points, segments = getPointsToPlotDF(obj, existGT, points, segments, Vertical, Horizontal)
    segments = segments + []
    return points, segments

def getPointsToPlotGT(obj, points, segments, Vertical, Horizontal):
    newPoints = points
    newSegments = segments
    if obj.ViewObject.LineScale > 0:
        sizeOfLine = obj.ViewObject.LineScale
    else:
        sizeOfLine = 1.0
    for i in range(len(obj.GT)):
        d = len(newPoints)
        if points[2].x < points[0].x:
            P0 = newPoints[-1] + Vertical * (sizeOfLine) if i == 0 else FreeCAD.Vector(newPoints[-2])
        else:
            P0 = newPoints[-1] + Vertical * (sizeOfLine) if i == 0 else FreeCAD.Vector(newPoints[-1])
        P1 = P0 + Vertical * (-sizeOfLine*2)
        P2 = P0 + Horizontal * (sizeOfLine*2)
        P3 = P1 + Horizontal * (sizeOfLine*2)
        lengthToleranceValue = len(stringencodecoin(displayExternal(obj.GT[i].ToleranceValue, obj.ViewObject.Decimals, 'Length', obj.ViewObject.ShowUnit)))
        if obj.GT[i].FeatureControlFrameIcon <> '':
            lengthToleranceValue += 2
        if obj.GT[i].Circumference:
            lengthToleranceValue += 2
        P4 = P2 + Horizontal * (sizeOfLine*lengthToleranceValue)
        P5 = P3 + Horizontal * (sizeOfLine*lengthToleranceValue)
        if obj.GT[i].DS == None or obj.GT[i].DS.Primary == None:
            newPoints = newPoints + [P0, P2, P3, P4, P5, P1]
            newSegments = newSegments + [-1, 0+d, 3+d, 4+d, 5+d, 0+d, -1, 1+d, 2+d]
            if points[2].x < points[0].x:
                displacement = newPoints[-3].x - newPoints[-6].x
                for i in range(len(newPoints)-6, len(newPoints)):
                    newPoints[i].x-=displacement
        else:
            P6 = P4 + Horizontal * (sizeOfLine*2)
            P7 = P5 + Horizontal * (sizeOfLine*2)
            if obj.GT[i].DS.Secondary <> None:
                P8 = P6 + Horizontal * (sizeOfLine*2)
                P9 = P7 + Horizontal * (sizeOfLine*2)
                if obj.GT[i].DS.Tertiary <> None:
                    P10 = P8 + Horizontal * (sizeOfLine*2)
                    P11 = P9 + Horizontal * (sizeOfLine*2)
                    newPoints = newPoints + [P0, P2, P3, P4, P5, P6, P7, P8, P9, P10, P11, P1]
                    newSegments = newSegments + [-1, 0+d, 9+d, 10+d, 11+d, 0+d, -1, 1+d, 2+d, -1, 3+d, 4+d, -1, 5+d, 6+d, -1, 7+d, 8+d]
                    if points[2].x < points[0].x:
                        displacement = newPoints[-3].x - newPoints[-12].x
                        for i in range(len(newPoints)-12, len(newPoints)):
                            newPoints[i].x-=displacement
                else:
                    newPoints = newPoints + [P0, P2, P3, P4, P5, P6, P7, P8, P9, P1]
                    newSegments = newSegments + [-1, 0+d, 7+d, 8+d, 9+d, 0+d, -1, 1+d, 2+d, -1, 3+d, 4+d, -1, 5+d, 6+d]
                    if points[2].x < points[0].x:
                        displacement = newPoints[-3].x - newPoints[-10].x
                        for i in range(len(newPoints)-10, len(newPoints)):
                            newPoints[i].x-=displacement
            else:
                newPoints = newPoints + [P0, P2, P3, P4, P5, P6, P7, P1]
                newSegments = newSegments + [-1, 0+d, 5+d, 6+d, 7+d, 0+d, -1, 1+d, 2+d, -1, 3+d, 4+d]
                if points[2].x < points[0].x:
                    displacement = newPoints[-3].x - newPoints[-8].x
                    for i in range(len(newPoints)-8, len(newPoints)):
                        newPoints[i].x-=displacement
    return newPoints, newSegments

def getPointsToPlotDF(obj, existGT, points, segments, Vertical, Horizontal):
    d = len(points)
    newPoints = points
    newSegments = segments
    if obj.ViewObject.LineScale > 0:
        sizeOfLine = obj.ViewObject.LineScale
    else:
        sizeOfLine = 1.0
    if not existGT:
        P0 = points[-1] + Vertical * (sizeOfLine)
        P1 = P0 + Horizontal * (sizeOfLine*2)
        P2 = P1 + Vertical * (-sizeOfLine*2)
        P3 = P2 + Horizontal * (-sizeOfLine*2)
        newPoints = newPoints + [P0, P1, P2, P3]
        newSegments = newSegments + [-1, 0+d, 1+d, 2+d, 3+d, 0+d]
        if points[2].x < points[0].x:
            displacement = newPoints[-2].x - newPoints[-1].x
            for i in range(len(newPoints)-4, len(newPoints)):
                newPoints[i].x-=displacement
    d=len(newPoints)
    P0 = newPoints[-1] + Horizontal * (sizeOfLine/2)
    P1 = P0 + Horizontal * (sizeOfLine)
    h = math.sqrt(sizeOfLine*sizeOfLine+(sizeOfLine/2)*(sizeOfLine/2))
    PAux = newPoints[-1] + Horizontal * (sizeOfLine)
    P2 = PAux + Vertical * (-h)
    P3 = PAux + Vertical * (-sizeOfLine*3)
    P4 = P3 + Horizontal * (sizeOfLine)
    P5 = P4 + Vertical * (-sizeOfLine*2)
    P6 = P5 + Horizontal * (-sizeOfLine*2)
    P7 = P6 + Vertical * (sizeOfLine*2)
    newPoints = newPoints + [P0, P1, P2, P3, P4, P5, P6, P7]
    newSegments = newSegments + [-1, 0+d, 2+d, -1, 1+d, 2+d, 3+d, 4+d, 5+d, 6+d, 7+d, 3+d]
    return newPoints, newSegments

def plotStrings(self, fp, points):
    import DraftGeomUtils
    if fp.ViewObject.LineScale > 0:
        sizeOfLine = fp.ViewObject.LineScale
    else:
        sizeOfLine = 1.0
    X = FreeCAD.Vector(1.0,0.0,0.0)
    Y = FreeCAD.Vector(0.0,1.0,0.0)
    Direction = X if abs(X.dot(fp.AP.Direction)) < 0.8 else Y
    Vertical = fp.AP.Direction.cross(Direction).normalize()
    Horizontal = Vertical.cross(fp.AP.Direction).normalize()
    index = 0
    indexIcon = 0
    displacement = 0
    if fp.GT <> []:
        for i in range(len(fp.GT)):
            distance = 0
            # posToleranceValue
            v = (points[7+displacement] - points[5+displacement])
            if v.x <> 0:
                distance = (v.x)/2
            elif v.y <> 0:
                distance = (v.y)/2
            else:
                distance = (v.z)/2
            if fp.GT[i].FeatureControlFrameIcon <> '':
                distance -= sizeOfLine
            if fp.GT[i].Circumference:
                distance += sizeOfLine
            centerPoint = points[5+displacement] + Horizontal * (distance)
            posToleranceValue = centerPoint + Vertical * (sizeOfLine/2)
            # posCharacteristic
            auxPoint = points[3+displacement] + Vertical * (-sizeOfLine*2)
            self.points[indexIcon].point.setValues([[auxPoint.x,auxPoint.y,auxPoint.z],[points[5+displacement].x,points[5+displacement].y,points[5+displacement].z],[points[4+displacement].x,points[4+displacement].y,points[4+displacement].z],[points[3+displacement].x,points[3+displacement].y,points[3+displacement].z]])
            self.face[indexIcon].numVertices = 4
            s = 1/(sizeOfLine*2)
            dS = FreeCAD.Vector(Horizontal) * s
            dT = FreeCAD.Vector(Vertical) * s
            self.svgPos[indexIcon].directionS.setValue(dS.x, dS.y, dS.z)
            self.svgPos[indexIcon].directionT.setValue(dT.x, dT.y, dT.z)
            displacementH = ((Horizontal*auxPoint)%(sizeOfLine*2))/(sizeOfLine*2)
            displacementV = ((Vertical*auxPoint)%(sizeOfLine*2))/(sizeOfLine*2)
            self.textureTransform[indexIcon].translation.setValue(-displacementH,-displacementV)
            filename = fp.GT[i].CharacteristicIcon
            filename = filename.replace(':/dd/icons', iconPath)
            self.svg[indexIcon].filename = str(filename)
            indexIcon+=1
            # posFeactureControlFrame
            if fp.GT[i].FeatureControlFrameIcon <> '':
                auxPoint1 = points[7+displacement] + Horizontal * (-sizeOfLine*2)
                auxPoint2 = auxPoint1 + Vertical * (sizeOfLine*2)
                self.points[indexIcon].point.setValues([[auxPoint1.x,auxPoint1.y,auxPoint1.z],[points[7+displacement].x,points[7+displacement].y,points[7+displacement].z],[points[6+displacement].x,points[6+displacement].y,points[6+displacement].z],[auxPoint2.x,auxPoint2.y,auxPoint2.z]])
                self.face[indexIcon].numVertices = 4
                self.svgPos[indexIcon].directionS.setValue(dS.x, dS.y, dS.z)
                self.svgPos[indexIcon].directionT.setValue(dT.x, dT.y, dT.z)
                displacementH = ((Horizontal*auxPoint1)%(sizeOfLine*2))/(sizeOfLine*2)
                displacementV = ((Vertical*auxPoint1)%(sizeOfLine*2))/(sizeOfLine*2)
                self.textureTransform[indexIcon].translation.setValue(-displacementH,-displacementV)
                filename = fp.GT[i].FeatureControlFrameIcon
                filename = filename.replace(':/dd/icons', iconPath)
                self.svg[indexIcon].filename = str(filename)
                indexIcon+=1
            # posDiameter
            if fp.GT[i].Circumference:
                auxPoint1 = points[5+displacement] + Horizontal * (sizeOfLine*2)
                auxPoint2 = auxPoint1 + Vertical * (sizeOfLine*2)
                self.points[indexIcon].point.setValues([[points[5+displacement].x,points[5+displacement].y,points[5+displacement].z],[auxPoint1.x,auxPoint1.y,auxPoint1.z],[auxPoint2.x,auxPoint2.y,auxPoint2.z],[points[4+displacement].x,points[4+displacement].y,points[4+displacement].z]])
                self.face[indexIcon].numVertices = 4
                self.svgPos[indexIcon].directionS.setValue(dS.x, dS.y, dS.z)
                self.svgPos[indexIcon].directionT.setValue(dT.x, dT.y, dT.z)
                displacementH = ((Horizontal*points[5+displacement])%(sizeOfLine*2))/(sizeOfLine*2)
                displacementV = ((Vertical*points[5+displacement])%(sizeOfLine*2))/(sizeOfLine*2)
                self.textureTransform[indexIcon].translation.setValue(-displacementH,-displacementV)
                filename = iconPath + '/diameter.svg'
                self.svg[indexIcon].filename = str(filename)
                indexIcon+=1

            self.textGT[index].string = self.textGT3d[index].string = stringencodecoin(displayExternal(fp.GT[i].ToleranceValue, fp.ViewObject.Decimals, 'Length', fp.ViewObject.ShowUnit))
            self.textGTpos[index].translation.setValue([posToleranceValue.x, posToleranceValue.y, posToleranceValue.z])
            self.textGT[index].justification = coin.SoAsciiText.CENTER
            index+=1
            displacement+=6
            if fp.GT[i].DS <> None and fp.GT[i].DS.Primary <> None:
                if fp.GT[i].FeatureControlFrameIcon <> '':
                    distance += (sizeOfLine*2)
                if fp.GT[i].Circumference:
                    distance -= (sizeOfLine*2)
                posPrimary = posToleranceValue + Horizontal * (distance+sizeOfLine)
                self.textGT[index].string = self.textGT3d[index].string = str(fp.GT[i].DS.Primary.Label)
                self.textGTpos[index].translation.setValue([posPrimary.x, posPrimary.y, posPrimary.z])
                self.textGT[index].justification = coin.SoAsciiText.CENTER
                index+=1
                displacement+=2
                if fp.GT[i].DS.Secondary <> None:
                    posSecondary = posPrimary + Horizontal * (sizeOfLine*2)
                    self.textGT[index].string = self.textGT3d[index].string = str(fp.GT[i].DS.Secondary.Label)
                    self.textGTpos[index].translation.setValue([posSecondary.x, posSecondary.y, posSecondary.z])
                    self.textGT[index].justification = coin.SoAsciiText.CENTER
                    index+=1
                    displacement+=2
                    if fp.GT[i].DS.Tertiary <> None:
                        posTertiary = posSecondary + Horizontal * (sizeOfLine*2)
                        self.textGT[index].string = self.textGT3d[index].string = str(fp.GT[i].DS.Tertiary.Label)
                        self.textGTpos[index].translation.setValue([posTertiary.x, posTertiary.y, posTertiary.z])
                        self.textGT[index].justification = coin.SoAsciiText.CENTER
                        index+=1
                        displacement+=2
        if fp.circumferenceBool and True in [l.Circumference for l in fp.GT]:
            # posDiameterTolerance
            auxPoint1 = FreeCAD.Vector(points[4])
            auxPoint2 = auxPoint1 + Horizontal * (sizeOfLine*2)
            auxPoint3 = auxPoint2 + Vertical * (sizeOfLine*2)
            auxPoint4 = auxPoint1 + Vertical * (sizeOfLine*2)
            self.points[indexIcon].point.setValues([[auxPoint1.x,auxPoint1.y,auxPoint1.z],[auxPoint2.x,auxPoint2.y,auxPoint2.z],[auxPoint3.x,auxPoint3.y,auxPoint3.z],[auxPoint4.x,auxPoint4.y,auxPoint4.z]])
            self.face[indexIcon].numVertices = 4
            self.svgPos[indexIcon].directionS.setValue(dS.x, dS.y, dS.z)
            self.svgPos[indexIcon].directionT.setValue(dT.x, dT.y, dT.z)
            displacementH = ((Horizontal*auxPoint1)%(sizeOfLine*2))/(sizeOfLine*2)
            displacementV = ((Vertical*auxPoint1)%(sizeOfLine*2))/(sizeOfLine*2)
            self.textureTransform[indexIcon].translation.setValue(-displacementH,-displacementV)
            filename = iconPath + '/diameter.svg'
            self.svg[indexIcon].filename = str(filename)
            indexIcon+=1
            posDiameterTolerance = auxPoint2 + Vertical * (sizeOfLine/2)
            self.textGT[index].justification = coin.SoAsciiText.LEFT
            self.textGTpos[index].translation.setValue([posDiameterTolerance.x, posDiameterTolerance.y, posDiameterTolerance.z])
            if fp.toleranceSelectBool:
                text = stringencodecoin(displayExternal(fp.diameter, fp.ViewObject.Decimals, 'Length', fp.ViewObject.ShowUnit) + ' +- ' + displayExternal(fp.toleranceDiameter, fp.ViewObject.Decimals, 'Length', fp.ViewObject.ShowUnit))
            else:
                text = stringencodecoin(displayExternal(fp.lowLimit, fp.ViewObject.Decimals, 'Length', fp.ViewObject.ShowUnit) + ' - ' + displayExternal(fp.highLimit, fp.ViewObject.Decimals, 'Length', fp.ViewObject.ShowUnit))
            self.textGT[index].string = self.textGT3d[index].string = text
            index+=1
        for i in range(index):
            try:
                DirectionAux = FreeCAD.Vector(fp.AP.Direction)
                DirectionAux.x = abs(DirectionAux.x)
                DirectionAux.y = abs(DirectionAux.y)
                DirectionAux.z = abs(DirectionAux.z)
                rotation=(DraftGeomUtils.getRotation(DirectionAux)).Q
                self.textGTpos[i].rotation.setValue(rotation)
            except:
                pass
        for i in range(index,len(self.textGT)):
            if str(self.textGT[i].string) <> "":
                self.textGT[i].string = self.textGT3d[i].string = ""
            else:
                break
        for i in range(indexIcon,len(self.svg)):
            if str(self.face[i].numVertices) <> 0:
                self.face[i].numVertices = 0
                self.svg[i].filename = ""
    else:
        for i in range(len(self.textGT)):
            if str(self.textGT[i].string) <> "" or str(self.svg[i].filename) <> "":
                self.textGT[i].string = self.textGT3d[i].string = ""
                self.face[i].numVertices = 0
                self.svg[i].filename = ""
            else:
                break
    if fp.DF <> None:
        self.textDF.string = self.textDF3d.string = str(fp.DF.Label)
        distance = 0
        v = (points[-3] - points[-2])
        if v.x <> 0:
            distance = (v.x)/2
        elif v.y <> 0:
            distance = (v.y)/2
        else:
            distance = (v.z)/2
        centerPoint = points[-2] + Horizontal * (distance)
        centerPoint = centerPoint + Vertical * (sizeOfLine/2)
        self.textDFpos.translation.setValue([centerPoint.x, centerPoint.y, centerPoint.z])
        try:
            DirectionAux = FreeCAD.Vector(fp.AP.Direction)
            DirectionAux.x = abs(DirectionAux.x)
            DirectionAux.y = abs(DirectionAux.y)
            DirectionAux.z = abs(DirectionAux.z)
            rotation=(DraftGeomUtils.getRotation(DirectionAux)).Q
            self.textDFpos.rotation.setValue(rotation)
        except:
            pass
    else:
        self.textDF.string = self.textDF3d.string = ""
    if fp.GT <> [] or fp.DF <> None:
        if len(fp.faces) > 1:
            # posNumFaces
            centerPoint = points[3] + Horizontal * (sizeOfLine)
            posNumFaces = centerPoint + Vertical * (sizeOfLine/2)
            self.textGT[index].string = self.textGT3d[index].string = (str(len(fp.faces))+'x')
            self.textGTpos[index].translation.setValue([posNumFaces.x, posNumFaces.y, posNumFaces.z])
            self.textGT[index].justification = coin.SoAsciiText.CENTER
            index+=1

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

    def onChanged(self, vobj, prop):
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
        obj.addProperty("App::PropertyFloat","Offset","GDT","The offset value to aply in this annotation plane")
        obj.addProperty("App::PropertyLinkSub","faces","GDT","Linked face of the object").faces = (getSelectionEx()[0].Object, getSelectionEx()[0].SubElementNames[0])
        obj.addProperty("App::PropertyVectorDistance","p1","GDT","Center point of Grid").p1 = obj.faces[0].Shape.getElement(obj.faces[1][0]).CenterOfMass
        obj.addProperty("App::PropertyVector","Direction","GDT","The normal direction of this annotation plane").Direction = obj.faces[0].Shape.getElement(obj.faces[1][0]).normalAt(0,0)
        obj.addProperty("App::PropertyVectorDistance","PointWithOffset","GDT","Center point of Grid with offset applied")

    def onChanged(self,vobj,prop):
        if hasattr(vobj,"PointWithOffset"):
            vobj.setEditorMode('PointWithOffset',1)

    def execute(self, fp):
        '''"Print a short message when doing a recomputation, this method is mandatory" '''
        fp.p1 = fp.faces[0].Shape.getElement(fp.faces[1][0]).CenterOfMass
        fp.Direction = fp.faces[0].Shape.getElement(fp.faces[1][0]).normalAt(0,0)

class _ViewProviderAnnotationPlane(_ViewProviderGDT):
    "A View Provider for the GDT AnnotationPlane object"
    def __init__(self, obj):
        _ViewProviderGDT.__init__(self,obj)

    def updateData(self, obj, prop):
        "called when the base object is changed"
        if prop in ["Point","Direction","Offset"]:
            obj.PointWithOffset = obj.p1 + obj.Direction * obj.Offset

    def doubleClicked(self,obj):
        showGrid()
        FreeCAD.DraftWorkingPlane.alignToPointAndAxis(self.Object.PointWithOffset, self.Object.Direction, 0)
        FreeCADGui.Snapper.grid.set()
        FreeCAD.ActiveDocument.recompute()

    def getIcon(self):
        return(":/dd/icons/annotationPlane.svg")

def makeAnnotationPlane(Name, Offset):
    ''' Explanation
    '''
    if len(getAllAnnotationPlaneObjects()) == 0:
        group = FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroupPython", "GDT")
        _GDTObject(group)
        _ViewProviderGDT(group.ViewObject)
    else:
        group = FreeCAD.ActiveDocument.getObject("GDT")

    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython","AnnotationPlane")
    _AnnotationPlane(obj)
    if gui:
        _ViewProviderAnnotationPlane(obj.ViewObject)
    obj.Label = Name
    obj.Offset = Offset
    group.addObject(obj)
    hideGrid()
    for l in getAllAnnotationObjects():
        l.touch()
    FreeCAD.ActiveDocument.recompute()
    return obj

    #-----------------------------------------------------------------------
    # Datum Feature
    #-----------------------------------------------------------------------

class _DatumFeature(_GDTObject):
    "The GDT DatumFeature object"
    def __init__(self, obj):
        _GDTObject.__init__(self,obj,"DatumFeature")

    def execute(self,obj):
        '''Do something when doing a recomputation, this method is mandatory'''
        pass

class _ViewProviderDatumFeature(_ViewProviderGDT):
    "A View Provider for the GDT DatumFeature object"
    def __init__(self, obj):
        _ViewProviderGDT.__init__(self,obj)

    def getIcon(self):
        return(":/dd/icons/datumFeature.svg")

def makeDatumFeature(Name, ContainerOfData):
    ''' Explanation
    '''
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython","DatumFeature")
    _DatumFeature(obj)
    if gui:
        _ViewProviderDatumFeature(obj.ViewObject)
    obj.Label = Name
    group = FreeCAD.ActiveDocument.getObject("GDT")
    group.addObject(obj)
    AnnotationObj = getAnnotationObj(ContainerOfData)
    if AnnotationObj == None:
        makeAnnotation(ContainerOfData.faces, ContainerOfData.annotationPlane, DF=obj, GT=[])
    else:
        faces = AnnotationObj.faces
        AP = AnnotationObj.AP
        GT = AnnotationObj.GT
        diameter = AnnotationObj.diameter
        toleranceSelect = AnnotationObj.toleranceSelectBool
        toleranceDiameter = AnnotationObj.toleranceDiameter
        lowLimit = AnnotationObj.lowLimit
        highLimit = AnnotationObj.highLimit
        group = makeAnnotation(faces, AP, DF=obj, GT=GT, modify = True, Object = AnnotationObj, diameter=diameter, toleranceSelect=toleranceSelect, toleranceDiameter=toleranceDiameter, lowLimit=lowLimit, highLimit=highLimit)
        group.addObject(obj)
    for l in getAllAnnotationObjects():
        l.touch()
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

    def updateData(self, obj, prop):
        "called when the base object is changed"
        if prop in ["Primary","Secondary","Tertiary"]:
            textName = obj.Label.split(":")[0]
            if obj.Primary <> None:
                textName+=': '+obj.Primary.Label
                if obj.Secondary <> None:
                    textName+=' | '+obj.Secondary.Label
                    if obj.Tertiary <> None:
                        textName+=' | '+obj.Tertiary.Label
            obj.Label = textName

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
    group = FreeCAD.ActiveDocument.getObject("GDT")
    group.addObject(obj)
    for l in getAllAnnotationObjects():
        l.touch()
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
        obj.addProperty("App::PropertyString","CharacteristicIcon","GDT","Characteristic icon path of the geometric tolerance")
        obj.addProperty("App::PropertyBool","Circumference","GDT","Indicates whether the tolerance applies to a given diameter")
        obj.addProperty("App::PropertyFloat","ToleranceValue","GDT","Tolerance value of the geometric tolerance")
        obj.addProperty("App::PropertyString","FeatureControlFrame","GDT","Feature control frame of the geometric tolerance")
        obj.addProperty("App::PropertyString","FeatureControlFrameIcon","GDT","Feature control frame icon path of the geometric tolerance")
        obj.addProperty("App::PropertyLink","DS","GDT","Datum system used")

    def onChanged(self,vobj,prop):
        "Do something when a property has changed"
        if hasattr(vobj,"CharacteristicIcon"):
            vobj.setEditorMode('CharacteristicIcon',2)
        if hasattr(vobj,"FeatureControlFrameIcon"):
            vobj.setEditorMode('FeatureControlFrameIcon',2)

class _ViewProviderGeometricTolerance(_ViewProviderGDT):
    "A View Provider for the GDT GeometricTolerance object"
    def __init__(self, obj):
        _ViewProviderGDT.__init__(self,obj)

    def getIcon(self):
        icon = self.Object.CharacteristicIcon
        return icon

def makeGeometricTolerance(Name, ContainerOfData):
    ''' Explanation
    '''
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython","GeometricTolerance")
    _GeometricTolerance(obj)
    if gui:
        _ViewProviderGeometricTolerance(obj.ViewObject)
    obj.Label = Name
    obj.Characteristic = ContainerOfData.characteristic.Label
    obj.CharacteristicIcon = ContainerOfData.characteristic.Icon
    obj.Circumference = ContainerOfData.circumference
    obj.ToleranceValue = ContainerOfData.toleranceValue
    obj.FeatureControlFrame = ContainerOfData.featureControlFrame.toolTip
    obj.FeatureControlFrameIcon = ContainerOfData.featureControlFrame.Icon
    obj.DS = ContainerOfData.datumSystem
    group = FreeCAD.ActiveDocument.getObject("GDT")
    group.addObject(obj)
    AnnotationObj = getAnnotationObj(ContainerOfData)
    if AnnotationObj == None:
        makeAnnotation(ContainerOfData.faces, ContainerOfData.annotationPlane, DF=None, GT=obj, diameter=ContainerOfData.diameter, toleranceSelect=ContainerOfData.toleranceSelect, toleranceDiameter=ContainerOfData.toleranceDiameter, lowLimit=ContainerOfData.lowLimit, highLimit=ContainerOfData.highLimit)
    else:
        gt=AnnotationObj.GT
        gt.append(obj)
        faces = AnnotationObj.faces
        AP = AnnotationObj.AP
        DF = AnnotationObj.DF
        if ContainerOfData.circumference:
            diameter = ContainerOfData.diameter
            toleranceSelect = ContainerOfData.toleranceSelect
            toleranceDiameter = ContainerOfData.toleranceDiameter
            lowLimit = ContainerOfData.lowLimit
            highLimit = ContainerOfData.highLimit
        else:
            diameter = AnnotationObj.diameter
            toleranceSelect = AnnotationObj.toleranceSelectBool
            toleranceDiameter = AnnotationObj.toleranceDiameter
            lowLimit = AnnotationObj.lowLimit
            highLimit = AnnotationObj.highLimit
        group = makeAnnotation(faces, AP, DF=DF, GT=gt, modify = True, Object = AnnotationObj, diameter=diameter, toleranceSelect=toleranceSelect, toleranceDiameter=toleranceDiameter, lowLimit=lowLimit, highLimit=highLimit)
        group.addObject(obj)
    for l in getAllAnnotationObjects():
        l.touch()
    FreeCAD.ActiveDocument.recompute()
    return obj

    #-----------------------------------------------------------------------
    # Annotation
    #-----------------------------------------------------------------------

class _Annotation(_GDTObject):
    "The GDT Annotation object"
    def __init__(self, obj):
        _GDTObject.__init__(self,obj,"Annotation")
        obj.addProperty("App::PropertyLinkSubList","faces","GDT","Linked faces of the object")
        obj.addProperty("App::PropertyLink","AP","GDT","Annotation plane used")
        obj.addProperty("App::PropertyLink","DF","GDT","Text").DF=None
        obj.addProperty("App::PropertyLinkList","GT","GDT","Text").GT=[]
        obj.addProperty("App::PropertyVectorDistance","p1","GDT","Start point")
        obj.addProperty("App::PropertyVector","Direction","GDT","The normal direction of your annotation plane")
        obj.addProperty("App::PropertyVector","selectedPoint","GDT","Selected point to where plot the annotation")
        obj.addProperty("App::PropertyBool","spBool","GDT","Boolean to confirm that a selected point exists").spBool = False
        obj.addProperty("App::PropertyBool","circumferenceBool","GDT","Boolean to determine if this annotation is over a circumference").circumferenceBool = False
        obj.addProperty("App::PropertyFloat","diameter","GDT","Diameter")
        obj.addProperty("App::PropertyBool","toleranceSelectBool","GDT","Determinates if use plus-minus or low and high limits").toleranceSelectBool = True
        obj.addProperty("App::PropertyFloat","toleranceDiameter","GDT","Diameter tolerance (Plus-minus)")
        obj.addProperty("App::PropertyFloat","lowLimit","GDT","Low limit diameter tolerance")
        obj.addProperty("App::PropertyFloat","highLimit","GDT","High limit diameter tolerance")

    def onChanged(self,obj,prop):
        if hasattr(obj,"spBool"):
            obj.setEditorMode('spBool',2)
        if hasattr(obj,"diameter"):
            if obj.circumferenceBool:
                obj.setEditorMode('diameter',0)
            else:
                obj.setEditorMode('diameter',2)
        if hasattr(obj,"toleranceDiameter") and hasattr(obj,"toleranceSelectBool"):
            if obj.circumferenceBool and obj.toleranceSelectBool:
                obj.setEditorMode('toleranceDiameter',0)
            else:
                obj.setEditorMode('toleranceDiameter',2)
        if hasattr(obj,"lowLimit") and hasattr(obj,"toleranceSelectBool"):
            if obj.circumferenceBool and not obj.toleranceSelectBool:
                obj.setEditorMode('lowLimit',0)
            else:
                obj.setEditorMode('lowLimit',2)
        if hasattr(obj,"highLimit") and hasattr(obj,"toleranceSelectBool"):
            if obj.circumferenceBool and not obj.toleranceSelectBool:
                obj.setEditorMode('highLimit',0)
            else:
                obj.setEditorMode('highLimit',2)

    def execute(self, fp):
        '''"Print a short message when doing a recomputation, this method is mandatory" '''
        # FreeCAD.Console.PrintMessage('Executed\n')
        auxP1 = fp.p1
        if fp.circumferenceBool:
            vertexex = fp.faces[0][0].Shape.getElement(fp.faces[0][1]).Vertexes
            fp.p1 = vertexex[0].Point if vertexex[0].Point.z > vertexex[1].Point.z else vertexex[1].Point
            fp.Direction = fp.AP.Direction
        else:
            fp.p1 = (fp.faces[0][0].Shape.getElement(fp.faces[0][1]).CenterOfMass).projectToPlane(fp.AP.PointWithOffset, fp.AP.Direction)
            fp.Direction = fp.faces[0][0].Shape.getElement(fp.faces[0][1]).normalAt(0,0)
        diff = fp.p1-auxP1
        if fp.spBool:
            fp.selectedPoint = fp.selectedPoint + diff

class _ViewProviderAnnotation(_ViewProviderGDT):
    "A View Provider for the GDT Annotation object"
    def __init__(self, obj):
        obj.addProperty("App::PropertyFloat","LineWidth","GDT","Line width").LineWidth = getLineWidth()
        obj.addProperty("App::PropertyColor","LineColor","GDT","Line color").LineColor = getRGBLine()
        obj.addProperty("App::PropertyFloat","LineScale","GDT","Line scale").LineScale = getParam("lineScale",1.0)
        obj.addProperty("App::PropertyLength","FontSize","GDT","Font size").FontSize = getTextSize()
        obj.addProperty("App::PropertyString","FontName","GDT","Font name").FontName = getTextFamily()
        obj.addProperty("App::PropertyColor","FontColor","GDT","Font color").FontColor = getRGBText()
        obj.addProperty("App::PropertyInteger","Decimals","GDT","The number of decimals to show").Decimals = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Units").GetInt("Decimals",2)
        obj.addProperty("App::PropertyBool","ShowUnit","GDT","Show the unit suffix").ShowUnit = getParam("showUnit",True)
        _ViewProviderGDT.__init__(self,obj)

    def attach(self, obj):
        "called on object creation"
        from pivy import coin
        self.node = coin.SoGroup()
        self.node3d = coin.SoGroup()
        self.lineColor = coin.SoBaseColor()
        self.textColor = coin.SoBaseColor()

        self.data = coin.SoCoordinate3()
        self.data.point.isDeleteValuesEnabled()
        self.lines = coin.SoIndexedLineSet()

        selectionNode = coin.SoType.fromName("SoFCSelection").createInstance()
        selectionNode.documentName.setValue(FreeCAD.ActiveDocument.Name)
        selectionNode.objectName.setValue(obj.Object.Name) # here obj is the ViewObject, we need its associated App Object
        selectionNode.subElementName.setValue("Lines")
        selectionNode.addChild(self.lines)

        self.font = coin.SoFont()
        self.font3d = coin.SoFont()
        self.textDF = coin.SoAsciiText()
        self.textDF3d = coin.SoText2()
        self.textDF.string = "" # some versions of coin crash if string is not set
        self.textDF3d.string = ""
        self.textDFpos = coin.SoTransform()
        self.textDF.justification = self.textDF3d.justification = coin.SoAsciiText.CENTER
        labelDF = coin.SoSeparator()
        labelDF.addChild(self.textDFpos)
        labelDF.addChild(self.textColor)
        labelDF.addChild(self.font)
        labelDF.addChild(self.textDF)
        labelDF3d = coin.SoSeparator()
        labelDF3d.addChild(self.textDFpos)
        labelDF3d.addChild(self.textColor)
        labelDF3d.addChild(self.font3d)
        labelDF3d.addChild(self.textDF3d)

        self.textGT = []
        self.textGT3d = []
        self.textGTpos = []
        self.svg = []
        self.svgPos = []
        self.points = []
        self.face = []
        self.textureTransform = []
        for i in range(20):
            self.textGT.append(coin.SoAsciiText())
            self.textGT3d.append(coin.SoText2())
            self.textGT[i].string = ""
            self.textGT3d[i].string = ""
            self.textGTpos.append(coin.SoTransform())
            self.textGT[i].justification = self.textGT3d[i].justification = coin.SoAsciiText.CENTER
            labelGT = coin.SoSeparator()
            labelGT.addChild(self.textGTpos[i])
            labelGT.addChild(self.textColor)
            labelGT.addChild(self.font)
            labelGT.addChild(self.textGT[i])
            labelGT3d = coin.SoSeparator()
            labelGT3d.addChild(self.textGTpos[i])
            labelGT3d.addChild(self.textColor)
            labelGT3d.addChild(self.font3d)
            labelGT3d.addChild(self.textGT3d[i])
            self.svg.append(coin.SoTexture2())
            self.face.append(coin.SoFaceSet())
            self.textureTransform.append(coin.SoTexture2Transform())
            self.svgPos.append(coin.SoTextureCoordinatePlane())
            self.face[i].numVertices = 0
            self.points.append(coin.SoVRMLCoordinate())
            image = coin.SoSeparator()
            image.addChild(self.svg[i])
            image.addChild(self.textureTransform[i])
            image.addChild(self.svgPos[i])
            image.addChild(self.points[i])
            image.addChild(self.face[i])
            self.node.addChild(labelGT)
            self.node3d.addChild(labelGT3d)
            self.node.addChild(image)
            self.node3d.addChild(image)

        self.drawstyle = coin.SoDrawStyle()
        self.drawstyle.style = coin.SoDrawStyle.LINES

        self.node.addChild(labelDF)
        self.node.addChild(self.drawstyle)
        self.node.addChild(self.lineColor)
        self.node.addChild(self.data)
        self.node.addChild(self.lines)
        self.node.addChild(selectionNode)
        obj.addDisplayMode(self.node,"2D")

        self.node3d.addChild(labelDF3d)
        self.node3d.addChild(self.lineColor)
        self.node3d.addChild(self.data)
        self.node3d.addChild(self.lines)
        self.node3d.addChild(selectionNode)
        obj.addDisplayMode(self.node3d,"3D")
        self.onChanged(obj,"LineColor")
        self.onChanged(obj,"LineWidth")
        self.onChanged(obj,"FontSize")
        self.onChanged(obj,"FontName")
        self.onChanged(obj,"FontColor")

    def updateData(self, fp, prop):
        "If a property of the handled feature has changed we have the chance to handle this here"
        # fp is the handled feature, prop is the name of the property that has changed
        if prop in "selectedPoint" and hasattr(fp.ViewObject,"Decimals") and hasattr(fp.ViewObject,"ShowUnit") and fp.spBool:
            points, segments = getPointsToPlot(fp)
            # print str(points)
            # print str(segments)
            self.data.point.setNum(len(points))
            cnt=0
            for p in points:
                self.data.point.set1Value(cnt,p.x,p.y,p.z)
                cnt=cnt+1
            self.lines.coordIndex.setNum(len(segments))
            self.lines.coordIndex.setValues(0,len(segments),segments)
            plotStrings(self, fp, points)
        if prop in "faces" and fp.faces <> []:
            fp.circumferenceBool = True if True in [l.Closed for l in fp.faces[0][0].Shape.getElement(fp.faces[0][1]).Edges] else False

    def doubleClicked(self,obj):
        select(self.Object)

    def getDisplayModes(self,obj):
        "Return a list of display modes."
        modes=[]
        modes.append("2D")
        modes.append("3D")
        return modes

    def getDefaultDisplayMode(self):
        "Return the name of the default display mode. It must be defined in getDisplayModes."
        return "2D"

    def setDisplayMode(self,mode):
        return mode

    def onChanged(self, vobj, prop):
        "Here we can do something when a single property got changed"
        if (prop == "LineColor") and hasattr(vobj,"LineColor"):
            if hasattr(self,"lineColor"):
                c = vobj.getPropertyByName("LineColor")
                self.lineColor.rgb.setValue(c[0],c[1],c[2])
        elif (prop == "LineWidth") and hasattr(vobj,"LineWidth"):
            if hasattr(self,"drawstyle"):
                w = vobj.getPropertyByName("LineWidth")
                self.drawstyle.lineWidth = w
        elif (prop == "FontColor") and hasattr(vobj,"FontColor"):
            if hasattr(self,"textColor"):
                c = vobj.getPropertyByName("FontColor")
                self.textColor.rgb.setValue(c[0],c[1],c[2])
        elif (prop == "FontSize") and hasattr(vobj,"FontSize"):
            if hasattr(self,"font"):
                if vobj.FontSize.Value > 0:
                    self.font.size = vobj.FontSize.Value
            if hasattr(self,"font3d"):
                if vobj.FontSize.Value > 0:
                    self.font3d.size = vobj.FontSize.Value*100
            vobj.Object.touch()
        elif (prop == "FontName") and hasattr(vobj,"FontName"):
            if hasattr(self,"font") and hasattr(self,"font3d"):
                self.font.name = self.font3d.name = str(vobj.FontName)
                vobj.Object.touch()
        else:
            self.updateData(vobj.Object, "selectedPoint")

    def getIcon(self):
        return(":/dd/icons/annotation.svg")

def makeAnnotation(faces, AP, DF=None, GT=[], modify=False, Object=None, diameter = 0.0, toleranceSelect = True, toleranceDiameter = 0.0, lowLimit = 0.0, highLimit = 0.0):
    ''' Explanation
    '''
    if not modify:
        obj = FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroupPython",dictionaryAnnotation[len(getAllAnnotationObjects())])
        _Annotation(obj)
        if gui:
            _ViewProviderAnnotation(obj.ViewObject)
        group = FreeCAD.ActiveDocument.getObject("GDT")
        group.addObject(obj)
        obj.faces = faces
        obj.AP = AP
        if obj.circumferenceBool:
            vertexex = obj.faces[0][0].Shape.getElement(obj.faces[0][1]).Vertexes
            index = [l.Point.z for l in vertexex].index(max([l.Point.z for l in vertexex]))
            obj.p1 = vertexex[index].Point
            obj.Direction = obj.AP.Direction
        else:
            obj.p1 = (obj.faces[0][0].Shape.getElement(obj.faces[0][1]).CenterOfMass).projectToPlane(obj.AP.PointWithOffset, obj.AP.Direction)
            obj.Direction = obj.faces[0][0].Shape.getElement(obj.faces[0][1]).normalAt(0,0)
    else:
        obj = Object
    obj.DF = DF
    obj.GT = GT
    obj.diameter = diameter
    obj.toleranceSelectBool = toleranceSelect
    if toleranceSelect:
        obj.toleranceDiameter = toleranceDiameter
        obj.lowLimit = 0.0
        obj.highLimit = 0.0
    else:
        obj.toleranceDiameter = 0.0
        obj.lowLimit = lowLimit
        obj.highLimit = highLimit

    def getPoint(point):
        if point:
            obj.spBool = True
            obj.selectedPoint = point
            hideGrid()
            obj.addObject(obj.DF) if obj.DF <> None else obj.addObject(obj.GT[0])
            select(obj)
            for l in getAllAnnotationObjects():
                l.touch()
            FreeCAD.ActiveDocument.recompute()
            return obj
        else:
            if DF:
                FreeCAD.ActiveDocument.removeObject(obj.DF.Name)
                if checkBoxState:
                    FreeCAD.ActiveDocument.removeObject(getAllDatumSystemObjects()[-1].Name)
            else:
                FreeCAD.ActiveDocument.removeObject(obj.GT[-1].Name)
            FreeCAD.ActiveDocument.removeObject(obj.Name)
            hideGrid()
            for l in getAllAnnotationObjects():
                l.touch()
            FreeCAD.ActiveDocument.recompute()
            return None
    if not obj.spBool:
        return FreeCADGui.Snapper.getPoint(callback=getPoint)
    else:
        hideGrid()
        select(obj)
        for l in getAllAnnotationObjects():
            l.touch()
        FreeCAD.ActiveDocument.recompute()
        return obj

    #-----------------------------------------------------------------------
    # Other classes
    #-----------------------------------------------------------------------

class Characteristics(object):
    def __init__(self, Label, Icon):
        self.Label = Label
        self.Icon = Icon
        self.Proxy = self

def makeCharacteristics(label=None):
    Label = ['Straightness', 'Flatness', 'Circularity', 'Cylindricity', 'Profile of a line', 'Profile of a surface', 'Perpendicularity', 'Angularity', 'Parallelism', 'Symmetry', 'Position', 'Concentricity','Circular run-out', 'Total run-out']
    Icon = [':/dd/icons/Characteristic/straightness.svg', ':/dd/icons/Characteristic/flatness.svg', ':/dd/icons/Characteristic/circularity.svg', ':/dd/icons/Characteristic/cylindricity.svg', ':/dd/icons/Characteristic/profileOfALine.svg', ':/dd/icons/Characteristic/profileOfASurface.svg', ':/dd/icons/Characteristic/perpendicularity.svg', ':/dd/icons/Characteristic/angularity.svg', ':/dd/icons/Characteristic/parallelism.svg', ':/dd/icons/Characteristic/symmetry.svg', ':/dd/icons/Characteristic/position.svg', ':/dd/icons/Characteristic/concentricity.svg',':/dd/icons/Characteristic/circularRunOut.svg', ':/dd/icons/Characteristic/totalRunOut.svg']
    if label == None:
        characteristics = Characteristics(Label, Icon)
        return characteristics
    else:
        index = Label.index(label)
        icon = Icon[index]
        characteristics = Characteristics(label, icon)
        return characteristics

class FeatureControlFrame(object):
    def __init__(self, Label, Icon, toolTip):
        self.Label = Label
        self.Icon = Icon
        self.toolTip = toolTip
        self.Proxy = self

def makeFeatureControlFrame(toolTip=None):
    Label = ['','','','','','','','']
    Icon = ['', ':/dd/icons/FeatureControlFrame/freeState.svg', ':/dd/icons/FeatureControlFrame/leastMaterialCondition.svg', ':/dd/icons/FeatureControlFrame/maximumMaterialCondition.svg', ':/dd/icons/FeatureControlFrame/projectedToleranceZone.svg', ':/dd/icons/FeatureControlFrame/regardlessOfFeatureSize.svg', ':/dd/icons/FeatureControlFrame/tangentPlane.svg', ':/dd/icons/FeatureControlFrame/unequalBilateral.svg']
    ToolTip = ['Feature control frame', 'Free state', 'Least material condition', 'Maximum material condition', 'Projected tolerance zone', 'Regardless of feature size', 'Tangent plane', 'Unequal Bilateral']
    if toolTip == None:
        featureControlFrame = FeatureControlFrame(Label, Icon, ToolTip)
        return featureControlFrame
    elif toolTip == '':
        featureControlFrame = FeatureControlFrame(Label[0], Icon[0], '')
        return featureControlFrame
    else:
        index = ToolTip.index(toolTip)
        icon = Icon[index]
        label = Label[index]
        featureControlFrame = FeatureControlFrame(label, icon, toolTip)
        return featureControlFrame

class ContainerOfData(object):
    def __init__(self, faces = []):
        self.faces = faces
        self.diameter = 0.0
        if self.faces <> []:
            self.Direction = self.faces[0][0].Shape.getElement(self.faces[0][1]).normalAt(0,0)
            self.DirectionAxis = self.faces[0][0].Shape.getElement(self.faces[0][1]).Surface.Axis
            self.p1 = self.faces[0][0].Shape.getElement(self.faces[0][1]).CenterOfMass
            try:
                edge = [l.Closed for l in self.faces[0][0].Shape.getElement(self.faces[0][1]).Edges].index(True)
                self.diameter = self.faces[0][0].Shape.getElement(self.faces[0][1]).Edges[edge].Length/pi
            except:
                pass
        self.circumference = False
        self.toleranceSelect = True
        self.toleranceDiameter = 0.0
        self.lowLimit = 0.0
        self.highLimit = 0.0
        self.OffsetValue = 0
        self.textName = ''
        self.textDS = ['','','']
        self.primary = None
        self.secondary = None
        self.tertiary = None
        self.characteristic = None
        self.toleranceValue = 0.0
        self.featureControlFrame = ''
        self.datumSystem = 0
        self.annotationPlane = 0
        self.annotation = None
        self.combo = ['','','','','','']
        self.Proxy = self

#---------------------------------------------------------------------------
# Customized widgets
#---------------------------------------------------------------------------

class GDTWidget:
    def __init__(self):
        self.dialogWidgets = []
        self.ContainerOfData = None

    def activate( self, idGDT=0, dialogTitle='GD&T Widget', dialogIconPath=':/dd/icons/GDT.svg', endFunction=None, dictionary=None):
        self.dialogTitle=dialogTitle
        self.dialogIconPath = dialogIconPath
        self.endFunction = endFunction
        self.dictionary = dictionary
        self.idGDT=idGDT
        self.ContainerOfData = makeContainerOfData()
        extraWidgets = []
        if dictionary <> None:
            extraWidgets.append(textLabelWidget(Text='Name:',Mask='NNNn', Dictionary=self.dictionary)) #http://doc.qt.io/qt-5/qlineedit.html#inputMask-prop
        else:
            extraWidgets.append(textLabelWidget(Text='Name:',Mask='NNNn'))
        self.taskDialog = GDTDialog( self.dialogTitle, self.dialogIconPath, self.idGDT, extraWidgets + self.dialogWidgets, self.ContainerOfData)
        FreeCADGui.Control.showDialog( self.taskDialog )

class GDTDialog:
    def __init__(self, title, iconPath, idGDT, dialogWidgets, ContainerOfData):
        self.initArgs = title, iconPath, idGDT, dialogWidgets, ContainerOfData
        self.createForm()

    def createForm(self):
        title, iconPath, idGDT, dialogWidgets, ContainerOfData = self.initArgs
        self.form = GDTGuiClass( title, idGDT, dialogWidgets, ContainerOfData)
        self.form.setWindowTitle( title )
        self.form.setWindowIcon( QtGui.QIcon( iconPath ) )

    def reject(self): #close button
        hideGrid()
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.Control.closeDialog()

    def getStandardButtons(self): #http://forum.freecadweb.org/viewtopic.php?f=10&t=11801
        return 0x00200000 #close button

class GDTGuiClass(QtGui.QWidget):

    def __init__(self, title, idGDT, dialogWidgets, ContainerOfData):
        super(GDTGuiClass, self).__init__()
        self.dd_dialogWidgets = dialogWidgets
        self.title = title
        self.idGDT = idGDT
        self.ContainerOfData = ContainerOfData
        self.initUI( self.title , self.idGDT, self.ContainerOfData)

    def initUI(self, title, idGDT, ContainerOfData):
        self.idGDT = idGDT
        self.ContainerOfData = ContainerOfData
        vbox = QtGui.QVBoxLayout()
        for widg in self.dd_dialogWidgets:
            if widg <> None:
                w = widg.generateWidget(self.idGDT,self.ContainerOfData)
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
        global auxDictionaryDS
        self.textName = self.ContainerOfData.textName.encode('utf-8')
        if self.idGDT == 1:
            obj = makeDatumFeature(self.textName, self.ContainerOfData)
            if checkBoxState:
                makeDatumSystem(auxDictionaryDS[len(getAllDatumSystemObjects())] + ': ' + self.textName, obj, None, None)
        elif self.idGDT == 2:
            separator = ' | '
            if self.ContainerOfData.textDS[0] <> '':
                if self.ContainerOfData.textDS[1] <> '':
                    if self.ContainerOfData.textDS[2] <> '':
                        self.textName = self.textName + ': ' + separator.join(self.ContainerOfData.textDS)
                    else:
                        self.textName = self.textName + ': ' + separator.join([self.ContainerOfData.textDS[0], self.ContainerOfData.textDS[1]])
                else:
                    self.textName = self.textName + ': ' + self.ContainerOfData.textDS[0]
            else:
                self.textName = self.textName
            makeDatumSystem(self.textName, self.ContainerOfData.primary, self.ContainerOfData.secondary, self.ContainerOfData.tertiary)
        elif self.idGDT == 3:
            makeGeometricTolerance(self.textName, self.ContainerOfData)
        elif self.idGDT == 4:
            makeAnnotationPlane(self.textName, self.ContainerOfData.OffsetValue)
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

    def generateWidget( self, idGDT, ContainerOfData ):
        self.idGDT = idGDT
        self.ContainerOfData = ContainerOfData
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
        self.ContainerOfData.textName = self.text.strip()
        return GDTDialog_hbox(self.Text,self.lineEdit)

    def valueChanged(self, argGDT):
        self.text = argGDT.strip()
        self.ContainerOfData.textName = self.text

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

    def generateWidget( self, idGDT, ContainerOfData ):
        self.idGDT = idGDT
        self.ContainerOfData = ContainerOfData
        FreeCAD.DraftWorkingPlane.alignToPointAndAxis(self.ContainerOfData.p1, self.ContainerOfData.Direction, 0.0)
        FreeCADGui.Snapper.grid.set()
        self.FORMAT = makeFormatSpec(0,'Length')
        self.uiloader = FreeCADGui.UiLoader()
        self.inputfield = self.uiloader.createWidget("Gui::InputField")
        self.inputfield.setText(self.FORMAT % 0)
        self.ContainerOfData.OffsetValue = 0
        QtCore.QObject.connect(self.inputfield,QtCore.SIGNAL("valueChanged(double)"),self.valueChanged)

        return GDTDialog_hbox(self.Text,self.inputfield)

    def valueChanged(self, d):
        self.ContainerOfData.OffsetValue = d
        FreeCAD.DraftWorkingPlane.alignToPointAndAxis(self.ContainerOfData.p1, self.ContainerOfData.Direction, self.ContainerOfData.OffsetValue)
        FreeCADGui.Snapper.grid.set()

class comboLabelWidget:
    def __init__(self, Text='Label', List=None, Icons=None, ToolTip = None):
        self.Text = Text
        self.List = List
        self.Icons = Icons
        self.ToolTip = ToolTip

    def generateWidget( self, idGDT, ContainerOfData ):
        self.idGDT = idGDT
        self.ContainerOfData = ContainerOfData

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

        self.ContainerOfData.combo[self.k] = QtGui.QComboBox()
        for i in range(len(self.List)):
            if self.Icons <> None:
                self.ContainerOfData.combo[self.k].addItem( QtGui.QIcon(self.Icons[i]), self.List[i] )
            else:
                if self.List[i] == None:
                    self.ContainerOfData.combo[self.k].addItem( '' )
                else:
                    self.ContainerOfData.combo[self.k].addItem( self.List[i].Label )
        if self.Text == 'Secondary:' or self.Text == 'Tertiary:':
            self.ContainerOfData.combo[self.k].setEnabled(False)
        if self.ToolTip <> None:
            self.ContainerOfData.combo[self.k].setToolTip( self.ToolTip[0] )
        self.comboIndex = self.ContainerOfData.combo[self.k].currentIndex()
        if self.k <> 0 and self.k <> 1:
            self.updateDate(self.comboIndex)
        self.ContainerOfData.combo[self.k].activated.connect(lambda comboIndex = self.comboIndex: self.updateDate(comboIndex))
        return GDTDialog_hbox(self.Text,self.ContainerOfData.combo[self.k])

    def updateDate(self, comboIndex):
        if self.ToolTip <> None:
            self.ContainerOfData.combo[self.k].setToolTip( self.ToolTip[comboIndex] )
        if self.Text == 'Primary:':
            self.ContainerOfData.textDS[0] = self.ContainerOfData.combo[self.k].currentText()
            self.ContainerOfData.primary = self.List[comboIndex]
            if comboIndex <> 0:
                self.ContainerOfData.combo[1].setEnabled(True)
            else:
                self.ContainerOfData.combo[1].setEnabled(False)
                self.ContainerOfData.combo[2].setEnabled(False)
                self.ContainerOfData.combo[1].setCurrentIndex(0)
                self.ContainerOfData.combo[2].setCurrentIndex(0)
                self.ContainerOfData.textDS[1] = ''
                self.ContainerOfData.textDS[2] = ''
                self.ContainerOfData.secondary = None
                self.ContainerOfData.tertiary = None
            self.updateItemsEnabled(self.k)
        elif self.Text == 'Secondary:':
            self.ContainerOfData.textDS[1] = self.ContainerOfData.combo[self.k].currentText()
            self.ContainerOfData.secondary = self.List[comboIndex]
            if comboIndex <> 0:
                self.ContainerOfData.combo[2].setEnabled(True)
            else:
                self.ContainerOfData.combo[2].setEnabled(False)
                self.ContainerOfData.combo[2].setCurrentIndex(0)
                self.ContainerOfData.textDS[2] = ''
                self.ContainerOfData.tertiary = None
            self.updateItemsEnabled(self.k)
        elif self.Text == 'Tertiary:':
            self.ContainerOfData.textDS[2] = self.ContainerOfData.combo[self.k].currentText()
            self.ContainerOfData.tertiary = self.List[comboIndex]
            self.updateItemsEnabled(self.k)
        elif self.Text == 'Characteristic:':
            self.ContainerOfData.characteristic = makeCharacteristics(self.List[comboIndex])
        elif self.Text == 'Datum system:':
            self.ContainerOfData.datumSystem = self.List[comboIndex]
        elif self.Text == 'Active annotation plane:':
            self.ContainerOfData.annotationPlane = self.List[comboIndex]
            self.ContainerOfData.Direction = self.List[comboIndex].Direction
            self.ContainerOfData.PointWithOffset = self.List[comboIndex].PointWithOffset
            FreeCAD.DraftWorkingPlane.alignToPointAndAxis(self.ContainerOfData.PointWithOffset, self.ContainerOfData.Direction, 0.0)
            FreeCADGui.Snapper.grid.set()

    def updateItemsEnabled(self, comboIndex):
        comboIndex0 = comboIndex
        comboIndex1 = (comboIndex+1) % 3
        comboIndex2 = (comboIndex+2) % 3

        for i in range(self.ContainerOfData.combo[comboIndex0].count()):
            self.ContainerOfData.combo[comboIndex0].model().item(i).setEnabled(True)
        if self.ContainerOfData.combo[comboIndex1].currentIndex() <> 0:
            self.ContainerOfData.combo[comboIndex0].model().item(self.ContainerOfData.combo[comboIndex1].currentIndex()).setEnabled(False)
        if self.ContainerOfData.combo[comboIndex2].currentIndex() <> 0:
            self.ContainerOfData.combo[comboIndex0].model().item(self.ContainerOfData.combo[comboIndex2].currentIndex()).setEnabled(False)
        for i in range(self.ContainerOfData.combo[comboIndex1].count()):
            self.ContainerOfData.combo[comboIndex1].model().item(i).setEnabled(True)
        if self.ContainerOfData.combo[comboIndex0].currentIndex() <> 0:
            self.ContainerOfData.combo[comboIndex1].model().item(self.ContainerOfData.combo[comboIndex0].currentIndex()).setEnabled(False)
        if self.ContainerOfData.combo[comboIndex2].currentIndex() <> 0:
            self.ContainerOfData.combo[comboIndex1].model().item(self.ContainerOfData.combo[comboIndex2].currentIndex()).setEnabled(False)
        for i in range(self.ContainerOfData.combo[comboIndex2].count()):
            self.ContainerOfData.combo[comboIndex2].model().item(i).setEnabled(True)
        if self.ContainerOfData.combo[comboIndex0].currentIndex() <> 0:
            self.ContainerOfData.combo[comboIndex2].model().item(self.ContainerOfData.combo[comboIndex0].currentIndex()).setEnabled(False)
        if self.ContainerOfData.combo[comboIndex1].currentIndex() <> 0:
            self.ContainerOfData.combo[comboIndex2].model().item(self.ContainerOfData.combo[comboIndex1].currentIndex()).setEnabled(False)

class groupBoxWidget:
    def __init__(self, Text='Label', List=[]):
        self.Text = Text
        self.List = List

    def generateWidget( self, idGDT, ContainerOfData ):
        self.idGDT = idGDT
        self.ContainerOfData = ContainerOfData
        self.group = QtGui.QGroupBox(self.Text)
        vbox = QtGui.QVBoxLayout()
        for l in self.List:
            vbox.addLayout(l.generateWidget(self.idGDT, self.ContainerOfData))
        self.group.setLayout(vbox)
        return self.group

class fieldLabeCombolWidget:
    def __init__(self, Text='Label', Circumference = [''], Diameter = 0.0, toleranceSelect = True, tolerance = 0.0, lowLimit = 0.0, highLimit = 0.0, List=[''], Icons=None, ToolTip = None):
        self.Text = Text
        self.Circumference = Circumference
        self.Diameter = Diameter
        self.toleranceSelect = toleranceSelect
        self.tolerance = tolerance
        self.lowLimit = lowLimit
        self.highLimit = highLimit
        self.List = List
        self.Icons = Icons
        self.ToolTip = ToolTip

    def generateWidget( self, idGDT, ContainerOfData ):
        self.idGDT = idGDT
        self.ContainerOfData = ContainerOfData
        self.DECIMALS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Units").GetInt("Decimals",2)
        self.FORMAT = makeFormatSpec(self.DECIMALS,'Length')
        self.AFORMAT = makeFormatSpec(self.DECIMALS,'Angle')
        self.uiloader = FreeCADGui.UiLoader()
        self.comboCircumference = QtGui.QComboBox()
        self.combo = QtGui.QComboBox()
        for i in range(len(self.Circumference)):
            self.comboCircumference.addItem(QtGui.QIcon(self.Circumference[i]), '' )
        self.comboCircumference.setSizeAdjustPolicy(QtGui.QComboBox.SizeAdjustPolicy(2))
        self.comboCircumference.setToolTip("Indicates whether the tolerance applies to a given diameter")
        self.combo.setSizeAdjustPolicy(QtGui.QComboBox.SizeAdjustPolicy(2))
        for i in range(len(self.List)):
            if self.Icons <> None:
                self.combo.addItem( QtGui.QIcon(self.Icons[i]), self.List[i] )
            else:
                self.combo.addItem( self.List[i] )
        if self.ToolTip <> None:
           self.updateDate()
        self.combo.activated.connect(self.updateDate)
        self.comboCircumference.activated.connect(self.updateDateCircumference)
        vbox = QtGui.QVBoxLayout()
        hbox1 = QtGui.QHBoxLayout()
        self.inputfield = self.uiloader.createWidget("Gui::InputField")
        self.inputfield.setText(self.FORMAT % 0)
        QtCore.QObject.connect(self.inputfield,QtCore.SIGNAL("valueChanged(double)"),self.valueChanged)
        hbox1.addWidget( QtGui.QLabel(self.Text) )
        hbox1.addWidget(self.comboCircumference)
        hbox1.addStretch(1)
        hbox1.addWidget(self.inputfield)
        hbox1.addStretch(1)
        hbox1.addWidget(self.combo)
        vbox.addLayout(hbox1)
        hbox2 = QtGui.QHBoxLayout()
        self.label = QtGui.QLabel('Diameter:')
        self.inputfield2 = self.uiloader.createWidget("Gui::InputField")
        auxText = displayExternal(self.Diameter,self.DECIMALS,'Length',True)
        self.inputfield2.setText(auxText)
        QtCore.QObject.connect(self.inputfield2,QtCore.SIGNAL("valueChanged(double)"),self.valueChangedDiameter)
        self.comboTolerance = QtGui.QComboBox()
        simbol = '±'
        self.comboTolerance.addItem( simbol[-1] )
        self.comboTolerance.addItem( 'Limit' )
        if self.toleranceSelect:
            self.comboTolerance.setCurrentIndex(0)
        else:
            self.comboTolerance.setCurrentIndex(1)
        self.updateDateTolerance
        self.comboTolerance.activated.connect(self.updateDateTolerance)
        self.labelTolerance = QtGui.QLabel(simbol[-1])
        self.labelLow = QtGui.QLabel('Low')
        self.labelHigh = QtGui.QLabel('High')
        self.inputfieldTolerance = self.uiloader.createWidget("Gui::InputField")
        auxText = displayExternal(self.tolerance,self.DECIMALS,'Length',True)
        self.inputfieldTolerance.setText(auxText)
        QtCore.QObject.connect(self.inputfieldTolerance,QtCore.SIGNAL("valueChanged(double)"),self.valueChangedTolerance)
        self.inputfieldLow = self.uiloader.createWidget("Gui::InputField")
        auxText = displayExternal(self.lowLimit,self.DECIMALS,'Length',True)
        self.inputfieldLow.setText(auxText)
        QtCore.QObject.connect(self.inputfieldLow,QtCore.SIGNAL("valueChanged(double)"),self.valueChangedLow)
        self.inputfieldHigh = self.uiloader.createWidget("Gui::InputField")
        auxText = displayExternal(self.highLimit,self.DECIMALS,'Length',True)
        self.inputfieldHigh.setText(auxText)
        QtCore.QObject.connect(self.inputfieldHigh,QtCore.SIGNAL("valueChanged(double)"),self.valueChangedHigh)

        hbox2.addWidget(self.label)
        hbox2.addStretch(1)
        hbox2.addWidget(self.inputfield2)
        vbox.addLayout(hbox2)
        hbox3 = QtGui.QHBoxLayout()
        hbox3.addWidget(self.comboTolerance)
        hbox3.addStretch(1)
        hbox3.addWidget(self.labelTolerance)
        hbox3.addWidget(self.inputfieldTolerance)
        hbox3.addWidget(self.labelLow)
        hbox3.addWidget(self.inputfieldLow)
        hbox3.addWidget(self.labelHigh)
        hbox3.addWidget(self.inputfieldHigh)
        vbox.addLayout(hbox3)
        self.label.hide()
        self.inputfield2.hide()
        self.label.hide()
        self.inputfield2.hide()
        self.comboTolerance.hide()
        self.labelTolerance.hide()
        self.inputfieldTolerance.hide()
        self.labelLow.hide()
        self.labelHigh.hide()
        self.inputfieldLow.hide()
        self.inputfieldHigh.hide()
        return vbox

    def updateDate(self):
        if self.ToolTip <> None:
            self.combo.setToolTip( self.ToolTip[self.combo.currentIndex()] )
        if self.Text == 'Tolerance value:':
            if self.combo.currentIndex() <> 0:
                self.ContainerOfData.featureControlFrame = makeFeatureControlFrame(self.ToolTip[self.combo.currentIndex()])
            else:
                self.ContainerOfData.featureControlFrame = makeFeatureControlFrame('')

    def updateDateCircumference(self):
        if self.comboCircumference.currentIndex() <> 0:
            self.ContainerOfData.circumference = True
            self.label.show()
            self.inputfield2.show()
            self.label.show()
            self.inputfield2.show()
            self.comboTolerance.show()
            if self.comboTolerance.currentIndex() == 0:
                self.labelTolerance.show()
                self.inputfieldTolerance.show()
            else:
                self.labelLow.show()
                self.labelHigh.show()
                self.inputfieldLow.show()
                self.inputfieldHigh.show()
        else:
            self.ContainerOfData.circumference = False
            self.label.hide()
            self.inputfield2.hide()
            self.label.hide()
            self.inputfield2.hide()
            self.comboTolerance.hide()
            if self.comboTolerance.currentIndex() == 0:
                self.labelTolerance.hide()
                self.inputfieldTolerance.hide()
            else:
                self.labelLow.hide()
                self.labelHigh.hide()
                self.inputfieldLow.hide()
                self.inputfieldHigh.hide()

    def updateDateTolerance(self):
        if self.comboTolerance.currentIndex() <> 0:
            self.ContainerOfData.toleranceSelect = False
            self.labelTolerance.hide()
            self.inputfieldTolerance.hide()
            self.labelLow.show()
            self.labelHigh.show()
            self.inputfieldLow.show()
            self.inputfieldHigh.show()
        else:
            self.ContainerOfData.toleranceSelect = True
            self.labelTolerance.show()
            self.inputfieldTolerance.show()
            self.labelLow.hide()
            self.labelHigh.hide()
            self.inputfieldLow.hide()
            self.inputfieldHigh.hide()

    def valueChanged(self,d):
        self.ContainerOfData.toleranceValue = d

    def valueChangedDiameter(self,d):
        self.ContainerOfData.diameter = d

    def valueChangedTolerance(self,d):
        self.ContainerOfData.toleranceDiameter = d

    def valueChangedLow(self,d):
        self.ContainerOfData.lowLimit = d

    def valueChangedHigh(self,d):
        self.ContainerOfData.highLimit = d

class CheckBoxWidget:
    def __init__(self, Text='Label'):
        self.Text = Text

    def generateWidget( self, idGDT, ContainerOfData ):
        self.idGDT = idGDT
        self.ContainerOfData = ContainerOfData
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

    def GetResources(self):
        return {
            'Pixmap' : ':/dd/icons/helpGDT.svg',
            'MenuText': 'Help',
            'ToolTip': 'Help'
            }

FreeCADGui.addCommand('dd_helpGDT', helpGDTCommand())
