# GeometricDimensioningAndTolerancing gui init module
#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2016 Juan Vañó Cerdá <juavacer@inf.upv.es>              *
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
import os
import GDT
import GDT_locator

global GDTWBpath
GDTWBpath = os.path.dirname(GDT_locator.__file__)

global main_DWB_Icon
GDTWB_icons_path =  os.path.join( GDTWBpath, 'Resources', 'icons')
main_DWB_Icon = os.path.join( GDTWB_icons_path , 'GDT.svg')

"""
    +-----------------------------------------------+
    |            Initialize the workbench           |
    +-----------------------------------------------+
"""
class GeometricDimensioningAndTolerancingWorkbench ( Workbench ):
    Icon = main_DWB_Icon
    MenuText = 'GD&T'
    ToolTip = 'Geometric Dimensioning & Tolerancing'

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def __init__(self):
        "This function is executed when FreeCAD starts"
        from PySide import QtGui
        GDTWB_fonts_path =  os.path.join( GDTWBpath, 'Resources', 'fonts')
        fontFile = os.path.join(GDTWB_fonts_path, "osifont-lgpl3fe.ttf")
        fontId = QtGui.QFontDatabase.addApplicationFont(fontFile)
        Msg ("{} Added as QtGui Font Id : {}\n".format(fontFile,fontId))
        fontFile = os.path.join(GDTWB_fonts_path, "Iso-Gps.ttf")
        fontId = QtGui.QFontDatabase.addApplicationFont(fontFile)
        Msg ("{} Added as QtGui Font Id : {}\n".format(fontFile,fontId))        
        pass

    """
    +-----------------------------------------------+
    |        This is where all is defined           |
    +-----------------------------------------------+
    """
    def Initialize(self):
        # load the module
        # import GD&T tools
        try:
            import datumFeature
            import datumSystem
            import geometricTolerance
            import annotationPlane
            import inventory
        except ImportError:
            FreeCAD.Console.PrintWarning("Error: Initializing one or more of the GD&T modules failed, GD&T will not work as expected.\n")


        """
        +-----------------------------------------------+
        |            Assembly Menu & Toolbar            |
        +-----------------------------------------------+
        """
        self.cmdList = ['dd_datumFeature','dd_datumSystem','dd_geometricTolerance','dd_annotationPlane']
        self.inventory = ['dd_inventory']
        # https://freecad.github.io/SourceDoc/d7/dc3/group__workbench.html
        self.appendToolbar("GD&T Tools",self.cmdList+self.inventory)  # Create ToolBar
        self.appendMenu("GD&T Tools",self.cmdList+self.inventory) # Create Menu

        FreeCADGui.addIconPath(':/dd/icons')
        FreeCADGui.addPreferencePage( ':/dd/ui/preferences-gdt.ui','GDT' )

        Log ("Loading Geometric Dimensioning & Tolerancing... done\n")

    def Activated(self):
        "This function is executed when the workbench is activated"
        Msg ("Geometric Dimensioning & Tolerancing workbench activated\n")

    def Deactivated(self):
        "This function is executed when the workbench is deactivated"
        Msg ("Geometric Dimensioning & Tolerancing workbench desactivated\n")

    """
    +-----------------------------------------------+
    |                Contextual Menus               |
    +-----------------------------------------------+
    """
    def ContextMenu(self, recipient):
        # "This is executed whenever the user right-clicks on screen"
        # "recipient" will be either "view" or "tree"
        showCmdList = True
        if FreeCADGui.Selection.getSelection():
            for i in range(len(FreeCADGui.Selection.getSelectionEx()[0].SubObjects)):
                if FreeCADGui.Selection.getSelectionEx()[0].SubObjects[i].ShapeType == 'Face':
                    pass
                else:
                    showCmdList = False
        else:
            showCmdList = False
        if showCmdList:
            self.appendContextMenu("", "Separator") # Add Separator 5@xes
            self.appendContextMenu("",self.cmdList) # add commands to the context menu
            
        self.appendContextMenu("",self.inventory)   # add inventory commands to the context menu
        self.appendContextMenu("", "Separator")     # Add Separator 5@xes

"""
+-----------------------------------------------+
|          actually make the workbench          |
+-----------------------------------------------+
"""
FreeCADGui.addWorkbench(GeometricDimensioningAndTolerancingWorkbench)
