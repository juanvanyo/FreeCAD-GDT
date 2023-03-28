

self.Direction = self.faces[0][0].Shape.getElement(self.faces[0][1]).normalAt(0,0)

FreeCADGui.Selection.getSelectionEx("",1)[0].Shape.getElement(FreeCADGui.Selection.getSelectionEx("",0)[0].SubElementNames[0])
FreeCADGui.Selection.getSelectionEx("",1)[0].Object.Shape.getElement(FreeCADGui.Selection.getSelectionEx()[0].SubElementNames[0]).normalAt(0,0)

FreeCADGui.Selection.getSelectionEx("",1)[0].Object.Shape.getElement(FreeCADGui.Selection.getSelectionEx("",1)[0].SubElementNames[0]).normalAt(0,0)

FreeCADGui.Selection.getSelectionEx("",1)[0].Object.Shape.getElement(FreeCADGui.Selection.getSelectionEx("",1)[0].SubElementNames[0]).CenterOfMass

# getSelectionEx

FreeCADGui.Selection.getSelectionEx("",0)[0].Object.Name
'Part'

FreeCADGui.Selection.getSelectionEx("",1)[0].Object.Name
'Pocket001'

FreeCADGui.Selection.getSelectionEx()[0].Object.Name
'Pocket001'


FreeCADGui.Selection.getSelectionEx("",0)[0].SubElementNames[0]
'Body.Pocket001.Face5'
 
FreeCADGui.Selection.getSelectionEx("",1)[0].SubElementNames[0]
'Face5'

## faces

objt = FreeCADGui.Selection.getSelectionEx("",0)[0].Object
c_name = FreeCADGui.Selection.getSelectionEx("",1)[0].SubElementNames[0]
vertexex = objt.Shape.getElement(c_name).Vertexes

c_face=objt.Shape.getElement(c_name)

c_face.Edges[0].Length
c_face.Surface.Axis

vertexex[0].Point
 
objt.Shape.getElement(c_name).normalAt(0,0)
Vector (0.0, 0.0, 1.0)




makeContainerOfData():
    ""
    faces = []
    for i in range(len(getSelectionEx())):
        for j in range(len(getSelectionEx()[i].SubElementNames)):
            faces.append((getSelectionEx()[i].Object, getSelectionEx()[i].SubElementNames[j]))
    faces.sort()
    container = ContainerOfData(faces)
    return container


class _AnnotationPlane(_GDTObject):
    "The GDT AnnotationPlane object"
    def __init__(self, obj):
        _GDTObject.__init__(self,obj,"AnnotationPlane")
        obj.addProperty("App::PropertyFloat","Offset","GDT","The offset value to aply in this annotation plane")
        obj.addProperty("App::PropertyLinkSub","faces","GDT","Linked face of the object").faces = (FreeCADGui.Selection.getSelectionEx("",0)[0].Object, FreeCADGui.Selection.getSelectionEx("",1)[0].SubElementNames[0])

