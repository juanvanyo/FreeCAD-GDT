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

from GDT import *

gdt = GDTWidget()
gdt.dialogWidgets.append( groupBoxWidget(Text='Constituents', List=[comboLabelWidget(Text='Primary:',List=[]),comboLabelWidget(Text='Secondary:',List=[]), comboLabelWidget(Text='Tertiary:',List=[])]) )

class DatumSystemCommand:
    def __init__(self):
        self.iconPath = ':/dd/icons/datumSystem.svg'
        self.toolTip = 'Add Datum System'
        self.dictionary = []
        for i in range(1,100):
            self.dictionary.append('DS'+str(i))
        self.idGDT = 2

    def Activated(self):
        listDF = [None] + getAllDatumFeatureObjects()
        gdt.dialogWidgets[0] = ( groupBoxWidget(Text='Constituents', List=[comboLabelWidget(Text='Primary:',List=listDF),comboLabelWidget(Text='Secondary:',List=listDF), comboLabelWidget(Text='Tertiary:',List=listDF)]) )
        gdt.activate(idGDT = self.idGDT, dialogTitle=self.toolTip, dialogIconPath=self.iconPath, endFunction=self.Activated, dictionary=self.dictionary)

    def GetResources(self):
        return {
            'Pixmap' : self.iconPath,
            'MenuText': self.toolTip,
            'ToolTip':  self.toolTip
            }

    def IsActive(self):
        if FreeCADGui.ActiveDocument:
            return len(getAllDatumFeatureObjects()) > 0
        else:
            return False

FreeCADGui.addCommand('dd_datumSystem', DatumSystemCommand())
