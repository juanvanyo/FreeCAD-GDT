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
import  DraftTools

gdt = GDTWidget()
dictionaryDF = []
dictionaryDF = map(chr, range(64, 91)) #64 because the first argument is not used
gdt.dialogWidgets.append( textLabelWidget(Text='Datum feature:',Mask='>A', Dictionary=dictionaryDF) ) #http://doc.qt.io/qt-5/qlineedit.html#inputMask-prop
gdt.dialogWidgets.append( comboLabelWidget(Text='Active annotation plane:', List=listAP) )
gdt.dialogWidgets.append( CheckBoxWidget(Text = 'Create corresponding Datum System') )

class DatumFeatureCommand:
    def __init__(self):
        self.iconPath = ':/dd/icons/datumFeature.svg'
        self.toolTip = 'Add Datum Feature'
        self.dictionary = []
        for i in range(100):
            self.dictionary.append('DF'+str(i))
        self.idGDT = 1

    def Activated(self):
        showGrid()
        gdt.activate(idGDT = self.idGDT, dialogTitle=self.toolTip, dialogIconPath=self.iconPath, endFunction=self.Activated, dictionary=self.dictionary)

    def GetResources(self):
        return {
            'Pixmap' : self.iconPath,
            'MenuText': self.toolTip,
            'ToolTip':  self.toolTip
            }

    def IsActive(self):
        global listAP
        if len(listAP) == 0:
            return False
        if getSelection():
            if len(getSelectionEx()[0].SubObjects) == 0:
                return False
            for i in range(len(getSelectionEx()[0].SubObjects)):
                if getSelectionEx()[0].SubObjects[i].ShapeType == 'Face':
                    pass
                else:
                    return False
        else:
            return False
        return True

FreeCADGui.addCommand('dd_datumFeature', DatumFeatureCommand())
