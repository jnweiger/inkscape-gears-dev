inkscape-extensions-gears-dev
=============================

Updated to use on inkscape 1.x

Enhanced version of the well known gears extension, allows spokes, center cross, metric module, best evolute shape ...

This is based on http://cnc-club.ru/forum/viewtopic.php?f=33&t=434&p=2594#p2500, with my own patches added ontop:

* extended_ranges.patch https://build.opensuse.org/package/view_file?expand=1&file=extended_ranges.patch&package=inkscape-extensions-gears-dev&project=home:jnweiger
* metric_module.patch https://build.opensuse.org/package/view_file?expand=1&file=metric_module.patch&package=inkscape-extensions-gears-dev&project=home:jnweiger
* selectable_accuracy.patch https://build.opensuse.org/package/view_file?expand=1&file=selectable_accuracy.patch&package=inkscape-extensions-gears-dev&project=home:jnweiger

Downloading:
* Easiest way is to download the Zip file and then extract on your machine to the proper directory.
* There will be two files: gears-dev.inx and gears-dev.py

Linux:
*  ~/.config/inkscape/extensions/ or
*  /usr/share/inkscape/extensions/

Windows: 
*  navigate to the directory %APPDATA%/inkscape/extensions

Mac OS X: 
*  ~/.config/inkscape/extensions/    (prefered)
*  /Applications/Inkscape.app/Contents/Resources/share/inkscape/extensions/

Path-correction for use with Laser-Cutters
==========================================
There are path offset functions in inkscape. The 'dynamic offset' feature works great, except that one has to use the mouse
to adjust an estimate of the offset. There is no way to enter an exaxt value in mm.

https://wiki.fablab-nuernberg.de/w/Ding:Zahnr%C3%A4der_mit_Inkscape#Werkzeug-Korrektur


References
==========

* http://wiki.inkscape.org/wiki/index.php/PythonEffectTutorial
* http://www.gizmology.net/gears.htm
* http://www.micro-machine-shop.com/gear_theory.pdf

