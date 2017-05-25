FreeCAD-GDT
===========

[![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)

Geometric Dimensioning and Tolerancing (GD&T) workbench for FreeCAD

Please see [forum thread](https://forum.freecadweb.org/viewtopic.php?f=10&t=22072) to discuss or report issues regarding this Addon with it's author and the FreeCAD community.

![screenshot](https://forum.freecadweb.org/download/file.php?id=36916)

Abstract
----------

The project is aimed at the development of a labeling software module for Geometric Dimensioning and Tolerancing (GD&T) in 2D and 3D technical drawings. The main contributions of this software are:

-	Allows the GD&T information to be added to the design itself, thus linking design, manufacturing and quality specifications.
-	Implements the ISO16792 standard for both 2D and 3D parts.
-	Incorporates a homogeneous graphical interface and integrated with the technical design tools and 3D.
-	There is no precedent developed as free software.

The implementation of the software is done as a module of the parametric modeling free software application [FreeCAD](http://freecadweb.org). This is a multiplatform project since the development of the module is done with Python and FreeCAD has compilations for multiple Operating Systems.

Installing
----------

Download and install your corresponding version of FreeCAD from [wiki Download page](http://www.freecadweb.org/wiki/Download) and either install
- automaticallu using the [FreeCAD Add-on Manager](https://github.com/FreeCAD/FreeCAD-addons) (bundled in to 0.17 dev version)
- manually by copying the FreeCAD-GDT folder to the Mod sub-directory of the FreeCAD application.

### Requirements

- Coin3D (4.0+) It is recommended to have Coin version 4.0 or higher installed but also works with version 3.0 but with some visual changes.

Operation of the module
----------

When doing a GD&T labeling, the first thing to do is to define an annotation plane on which the annotations we make will be painted. To do this, first select a face of the piece and click the command on the toolbar add annotation plane. This will define a plane on that face and we can also apply an offset to place our annotation plane to the height we want in parallel on the selected face. Defining an annotation plane.

The next step we must do is to create a datum reference or a geometric tolerance. Although it is important to note that if the first thing to be created is a geometric tolerance, it can not contain any datum system since there will not be any created yet. However, this can be added later by modifying the geometric tolerance from the inventory of GD&T elements.

In any case, when creating a datum reference or a geometric characteristic, the user must choose some parameters that will define the element to be created. These include the annotation plane on which the annotation will be represented. Everything followed should select a point on the plane. Point on which will start the representation of the frame that will encapsulate the data of our annotation.

In addition, at any time, you can create a datum system with the datum reference elements that have been created and this system can be applied to the geometric tolerances that we consider appropriate. This will indicate that said geometric tolerance will be applied to the face or faces corresponding to the annotation with respect to the datum references that make up the associated datum system.

Subsequently, if you want to apply a datum reference or a geometric tolerance to a face or faces that already have an annotation associated with it, this module will automatically detect which annotation is and it will add the new element to that annotation.

Therefore, the running of our module could be summarized in that we have to add geometric tolerances to our design but in order to carry this out, we would first have to create different elements like annotation planes to place our annotation in the desired place, or Datum references and datum systems to provide necessary information to our geometric tolerances. So we have to create different elements until we have our piece completely labeled with all the geometric tolerances that we need to indicate.

Commands
----------

- ![Add Annotation Plane](https://forum.freecadweb.org/download/file.php?id=36932) Add Annotation Plane
- ![Add Datum Feature](https://forum.freecadweb.org/download/file.php?id=36933) Add Datum Feature
- ![Add Annotation System](https://forum.freecadweb.org/download/file.php?id=36934) Add Annotation System
- ![Add Geometric Tolerance](https://forum.freecadweb.org/download/file.php?id=36935) Add Geometric Tolerance
- ![Inventory of the elements of GD&T](https://forum.freecadweb.org/download/file.php?id=36936) Inventory of the elements of GD&T

----

### :scroll: License ? [![GitHub license](https://img.shields.io/github/license/juanvanyo/FreeCAD-GDT.svg)](https://github.com/juanvanyo/FreeCAD-GDT/blob/master/LICENSE)
