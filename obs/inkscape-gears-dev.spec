#
# spec file for package 
#
# Copyright (c) 2013 SUSE LINUX Products GmbH, Nuernberg, Germany.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via https://github.com/jnweiger/inkscape-gears-dev/issues
#


Name:           inkscape-gears-dev
Version:        20140403_0.7jw
Release:        0
Summary:        An improved version of the gears plugin
License:        GPL-2.0+
Group:          Development/Languages/Python
Url:            git@github.com:jnweiger/inkscape-gears-dev.git
# Url1:         http://cnc-club.ru/forum/viewtopic.php?f=33&t=434&p=2594#p2500
# Url2:		https://bugs.launchpad.net/inkscape/+bug/707290
Source1:        https://bugs.launchpad.net/inkscape/+bug/707290/+attachment/2628055/+files/gears-dev.tar.gz
Source0:        https://github.com/jnweiger/inkscape-gears-dev/archive/inkscape-gears-dev-master.zip
Patch1:		metric_module.patch
Patch2:		extended_ranges.patch
Patch3:		selectable_accuracy.patch
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
BuildArch:      noarch
BuildRequires:  unzip

%description
An inkscape plugin for rendering gears. This gears-dev extension is an enhancement of 
the stock gears extension that ships with inkscape. 

- Our version handles bosth metric module and circular pitch,
- Central hole for the shaft and some radial holes (and spokes) to make gear lighter.
- More accurate tooth profile. Selecting automatic, or low/med/high with up to 20 points per tooth.
- Center cross (easy for aligning); off by default, can be turned on
- The rotational center is now in the center of the gear, not in the center of the bounding box.
- Pitch circle (easy for meshing; circles should touch for meshing gears); off by defalut can be turned on
- Info: in the SVG there is now an extra field telling a little about the gear (easy if you want to make a meshing gear but you forgot the settings used)
- Annotation text is available for easier debugging.
- included an option to render rack gear.

Authors
-------
	Nick (lp:~xepecine)
	Gijs van Oort (lp:~gijsvanoort)
        Jürgen Weigert (juewei@fabmail.org)
        Mark Schafer <mschafer@wireframe.biz>


%prep
#% setup -T -c -n %name -a 0
%setup -n inkscape-gears-dev-master
# # metric_module.patch
# %patch1 -p1
# # extended_ranges.patch
# %patch2 -p1
# # selectable_accuracy.patch
# %patch3 -p1

%build

%install
install -d -m 755            %{buildroot}%{_datadir}/inkscape/extensions/
install -m 644 gears-dev.inx %{buildroot}%{_datadir}/inkscape/extensions/
install -m 755 gears-dev.py  %{buildroot}%{_datadir}/inkscape/extensions/

%files
%defattr(-,root,root,-)
%dir %{_datadir}/inkscape
%dir %{_datadir}/inkscape/extensions
%{_datadir}/inkscape/extensions/*

%changelog

