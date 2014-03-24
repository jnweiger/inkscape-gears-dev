#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
Copyright (C) 2007 Aaron Spike  (aaron @ ekips.org)
Copyright (C) 2007 Tavmjong Bah (tavmjong @ free.fr)
Copyright (C) http://cnc-club.ru/forum/viewtopic.php?f=33&t=434&p=2594#p2500
Copyright (C) 2014 Jürgen Weigert (juewei@fabfolk.com)

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

2014-04-20: jw@suse.de 0.2  Option --accuracy=0 for automatic added.
2014-04-21: sent upstream: https://bugs.launchpad.net/inkscape/+bug/1295641
2014-04-21: jw@suse.de 0.3  Fixed center of rotation for gears with odd number of teeth.
'''
import inkex
import simplestyle, sys, os
from math import *

__version__ = '0.4'

def linspace(a,b,n):
	return [a+x*(b-a)/(n-1) for x in range(0,n)]

def involute_intersect_angle(Rb, R):
	Rb, R = float(Rb), float(R)
	return (sqrt(R**2 - Rb**2) / (Rb)) - (acos(Rb / R))

def point_on_circle(radius, angle):
	x = radius * cos(angle)
	y = radius * sin(angle)
	return (x, y)

def points_to_bbox(p):
        llx = urx = p[0][0]
        lly = ury = p[0][1]
        for x in p[1:]:
          if   x[0] < llx: llx = x[0]
          elif x[0] > urx: urx = x[0]
          if   x[1] < lly: lly = x[1]
          elif x[1] > ury: ury = x[1]
        return (llx, lly, urx, ury)

def points_to_bbox_center(p):
        bbox = points_to_bbox(p)
        return ((bbox[0]+bbox[2])/2., (bbox[1]+bbox[3])/2.)
                
def points_to_svgd(p):
	f = p[0]
	p = p[1:]
	svgd = 'M%.4f,%.4f' % f
	for x in p:
		svgd += 'L%.4f,%.4f' % x
        svgd += 'z'
	return svgd

def draw_SVG_circle(r, cx, cy, fill, strokewidth, name, parent):
    style = { 'stroke': '#000000', 'fill': fill, 'stroke-width':strokewidth }
    circ_attribs = {'style':simplestyle.formatStyle(style),
                    'cx':str(cx), 'cy':str(cy), 
                    'r':str(r),
                    inkex.addNS('label','inkscape'):name}
    circle = inkex.etree.SubElement(parent, inkex.addNS('circle','svg'), circ_attribs )
    

def generate_rack_path(tooth_count, module, pressure_angle,
                       base_height, tab_length, clearance=0, draw_guides=False):
        """ Just draw the rack """
        pitch = module / pi
        pitch_diameter = tooth_count * pitch
        addendum = pitch_diameter / tooth_count
        spacing = addendum * 1.414 # absolutely not right - should be using pitch and a proper algorithm
        # generate points: list of (x, y) pairs
        points = []
        x = -tooth_count * spacing - tab_length # center rack in drawing
        tas = tan(radians(pressure_angle)) * spacing
        #inkex.debug("angle=%s spacing=%s"%(pressure_angle, spacing))
        # Start with base tab on LHS
        points.append((x, base_height))
        points.append((x, 0))
        x += tab_length
        points.append((x, 0))
        # An involute on a circle of infinite radius is a simple linear ramp.
        # We need to add curve at bottom and use clearance.
        for i in range(tooth_count):
            # move along path, generating the next 'tooth'
            points.append((x, 0))
            points.append((x + tas, -spacing))
            points.append((x + spacing, -spacing))
            points.append((x + spacing + tas, 0))
            x += spacing * 2.0
        x -= spacing - tas # remove last adjustment
        # add base on RHS
        points.append((x, 0))
        x += tab_length
        points.append((x, 0))
        points.append((x, base_height)) # add end tab
        # return ready for use in an SVG 'path'
        return points_to_svgd(points)


class Gears(inkex.Effect):
	def __init__(self):
		inkex.Effect.__init__(self)
                try:
                  self.tty = open("/dev/tty", 'w')
                except:
                  self.tty = open(os.devnull, 'w')  # '/dev/null' for POSIX, 'nul' for Windows.
                # print >>self.tty, "gears-dev " + __version__
		self.OptionParser.add_option("-t", "--teeth",
						action="store", type="int",
						dest="teeth", default=24,
						help="Number of teeth")
		
		self.OptionParser.add_option("-M", "--metric_or_pitch",
                                                action="store", type="string", 
                                                dest="metric_or_pitch", default='useCP',
                                                help="Traditional or Metric")
		
		self.OptionParser.add_option("-p", "--pitch",
						action="store", type="float",
						dest="pitch", default=20.0,
						help="Circular Pitch (length of arc from one tooth to next) or Metric Module")

		self.OptionParser.add_option("-m", "--module",
						action="store", type="float", 
						dest="module", default=2.5,
						help="Metric Module - ratio of diameter/teeth")

		self.OptionParser.add_option("-a", "--angle",
						action="store", type="float",
						dest="angle", default=20.0,
						help="Pressure Angle (common values: 14.5, 20, 25 degrees)")

		self.OptionParser.add_option("-u", "--units",
						action="store", type="float",
						dest="units", default=0.0,
						help="Units 1=px (default unless --metric), 3.5433070866=mm")

		self.OptionParser.add_option("-A", "--accuracy",
						action="store", type="int",
						dest="accuracy", default=0,
						help="Accuracy of involute: automatic: 5..20 (default), best: 20(default), medium 10, low: 5; good acuracy is important with a low tooth count")
                # Clearance: Radial distance between top of tooth on one gear to bottom of gap on another.
                self.OptionParser.add_option("", "--clearance",
						action="store", type="float",
						dest="clearance", default=0.0,
						help="Clearance between bottom of gap of this gear and top of tooth of another")

                self.OptionParser.add_option("", "--annotation",
						action="store", type="inkbool", 
						dest="annotation", default=False,
						help="Draw annotation text")
                

		self.OptionParser.add_option("", "--mount-hole",
						action="store", type="float",
						dest="mount_hole", default=5,
						help="Mount hole diameter")

		self.OptionParser.add_option("", "--mount_radius",
						action="store", type="float",
						dest="mount_radius", default=15,
						help="Mount support radius")

		self.OptionParser.add_option("", "--holes-count",
						action="store", type="int",
						dest="holes_count", default=24,
						help="Holes count")

		self.OptionParser.add_option("", "--holes-border",
						action="store", type="float",
						dest="holes_border", default=5,
						help="Holes border width")

		self.OptionParser.add_option("", "--holes-rounding",
						action="store", type="float",
						dest="holes_rounding", default=5,
						help="Holes rounding")

		self.OptionParser.add_option("", "--active-tab",
						action="store", type="string",
						dest="active_tab", default='',
						help="Active tab. Not used now.")
						
		self.OptionParser.add_option("-x", "--centercross",
						action="store", type="inkbool", 
						dest="centercross", default=False,
						help="Draw cross in center")
		self.OptionParser.add_option("-c", "--pitchcircle",
						action="store", type="inkbool",
						dest="pitchcircle", default=False,
						help="Draw pitch circle (for mating)")

                self.OptionParser.add_option("-r", "--drawrack",
						action="store", type="inkbool", 
						dest="drawrack", default=False,
						help="Draw Rack gear")
		self.OptionParser.add_option("", "--teeth_length",
						action="store", type="int",
						dest="teeth_length", default=12,
						help="Length (in teeth) of rack.")
                self.OptionParser.add_option("", "--base_height",
						action="store", type="float",
						dest="base_height", default=8,
						help="Height of Base")
                self.OptionParser.add_option("", "--base_tab",
						action="store", type="float",
						dest="base_tab", default=14,
						help="Length of tabs on ends")

		
        def add_text(self, node, text, position, text_height=12):
                txt_style = {'font-size': '%dpx' % text_height, 'font-style':'normal', 'font-weight': 'normal',
                             'fill': '#F6921E', 'font-family': 'Bitstream Vera Sans,sans-serif',
                             'text-anchor': 'middle', 'text-align': 'center'}
                txt_attribs = {inkex.addNS('label','inkscape'): 'Annotation',
                               'style': simplestyle.formatStyle(txt_style),
                               'x': str(position[0]),
                               'y': str((position[1] + text_height) * 1.2)
                               }
                txt = inkex.etree.SubElement(node, inkex.addNS('text','svg'), txt_attribs)
                txt.text = text
                

	def effect(self):
                """ Calculate Gear factors from inputs.
                    - Make list of radii, angles, and centers for each tooth and iterate through them
                    - Turn on other visual features e.g. cross, rack, annotations, etc
                """
                # Debug using:  inkex.debug( "angle=%s pitch=%s" % (angle, pitch) )
		accuracy1 = 20 # Number of points of the involute curve
		accuracy2 = 9  # Number of points on circular parts
		units = self.options.units
		teeth = self.options.teeth 
		metric_module = self.options.metric_or_pitch == 'useMetric'
		if self.options.accuracy is not None:
                        if self.options.accuracy == 0:  
                            # automatic
                            if   teeth < 10: accuracy1 = 20
                            elif teeth < 30: accuracy1 = 12
                            else:            accuracy1 = 6
			else:
                            accuracy1 = self.options.accuracy
			accuracy2 = int(self.options.accuracy)/2 - 1
			if accuracy2 < 3: accuracy2 = 3

                if units == 0.0:
                        if metric_module:
                                units = 3.5433070866 # ??
                        else:
                                units = 1
                #
                if metric_module:
                        # options.pitch is metric modules, we need circular pitch
		        pitch = self.options.module * units * pi
                else:
		        pitch = self.options.pitch * units
		angle = self.options.angle # Angle of tangent to tooth at circular pitch wrt radial line.

		mount_hole = self.options.mount_hole * units
		mount_radius = self.options.mount_radius * units

		holes_count = self.options.holes_count
		holes_rounding = self.options.holes_rounding * units
		holes_border = self.options.holes_border * units
		centercross = self.options.centercross # draw center or not (boolean)
		pitchcircle = self.options.pitchcircle # draw pitch circle or not (boolean)
		clearance = self.options.clearance * units
		
		# print >>sys.stderr, "Teeth: %s\n"		% teeth

		two_pi = 2.0 * pi

		# Pitch (circular pitch): Length of the arc from one tooth to the next)
		# Pitch diameter: Diameter of pitch circle.
		pitch_diameter = float( teeth ) * pitch / pi
		pitch_radius   = pitch_diameter / 2.0

		# Base Circle
		base_diameter = pitch_diameter * cos( radians( angle ) )
		base_radius   = base_diameter / 2.0

		# Diametrial pitch: Number of teeth per unit length.
		pitch_diametrial = float( teeth )/ pitch_diameter

		# Addendum: Radial distance from pitch circle to outside circle.
		addendum = 1.0 / pitch_diametrial

		# Outer Circle
		outer_radius = pitch_radius + addendum
		outer_diameter = outer_radius * 2.0

		# Tooth thickness: Tooth width along pitch circle.
		tooth  = ( pi * pitch_diameter ) / ( 2.0 * float( teeth ) )

		# Undercut?
		undercut = (2.0 / ( sin( radians( angle ) ) ** 2))
		needs_undercut = teeth < undercut


		# Clearance: Radial distance between top of tooth on one gear to bottom of gap on another.
		# Is now a parameter
		#clearance = 0.0

		# Dedendum: Radial distance from pitch circle to root diameter.
		dedendum = addendum + clearance

		# Root diameter: Diameter of bottom of tooth spaces. 
		root_radius =  pitch_radius - dedendum
		root_diameter = root_radius * 2.0

		half_thick_angle = two_pi / (4.0 * float( teeth ) )
		pitch_to_base_angle  = involute_intersect_angle( base_radius, pitch_radius )
		pitch_to_outer_angle = involute_intersect_angle( base_radius, outer_radius ) - pitch_to_base_angle

		start_involute_radius = max(base_radius, root_radius)
		radii = linspace(start_involute_radius,outer_radius,accuracy1)
		angles = [ involute_intersect_angle(base_radius, r) for r in radii]

		centers = [(x * two_pi / float( teeth) ) for x in range( teeth ) ]
		points = []

		for c in centers:
			# Angles
			pitch1 = c - half_thick_angle
			base1  = pitch1 - pitch_to_base_angle
			offsetangles1 = [ base1 + x for x in angles]
			points1 = [ point_on_circle( radii[i], offsetangles1[i]) for i in range(0,len(radii)) ]

			pitch2 = c + half_thick_angle
			base2  = pitch2 + pitch_to_base_angle
			offsetangles2 = [ base2 - x for x in angles] 
			points2 = [ point_on_circle( radii[i], offsetangles2[i]) for i in range(0,len(radii)) ]

			points_on_outer_radius = [ point_on_circle(outer_radius, x) for x in linspace(offsetangles1[-1],offsetangles2[-1],accuracy2)]

			if root_radius > base_radius:
				pitch_to_root_angle = pitch_to_base_angle - involute_intersect_angle(base_radius, root_radius )
				root1 = pitch1 - pitch_to_root_angle
				root2 = pitch2 + pitch_to_root_angle
				points_on_root = [point_on_circle ( root_radius, x) for x in linspace(root2,root1+(two_pi/float(teeth)),accuracy2)]
				p_tmp = points1 + points_on_outer_radius[1:-1] + points2[::-1] + points_on_root[1:-1] # [::-1] reverses list; [1:-1] removes first and last element
			else:
				points_on_root = [point_on_circle ( root_radius, x) for x in linspace(base2,base1+(two_pi/float(teeth)),accuracy2)]
				p_tmp = points1 + points_on_outer_radius[1:-1] + points2[::-1] + points_on_root # [::-1] reverses list

			points.extend( p_tmp )

		path = points_to_svgd( points )
		bbox_center = points_to_bbox_center( points )
                # print >>self.tty, bbox_center

		# Holes
		holes = ''
		r_outer = root_radius - holes_border
		for i in range(holes_count):
			points = []
			start_a, end_a = i*2*pi/holes_count, (i+1)*2*pi/holes_count
			a = asin(holes_border/mount_radius/2)
			points += [ point_on_circle(mount_radius,start_a+a), point_on_circle(mount_radius,end_a-a)]
                        try:
			    a = asin(holes_border/r_outer/2)
                        except:
                            print >> sys.stderr, "error: Holes border width is too large:", holes_border/units, "max=", r_outer*2/units
                            
			points += [point_on_circle(r_outer,end_a-a), point_on_circle(r_outer,start_a+a) ]

			path += (
					"M %f,%f" % points[0] +
					"A  %f,%f %s %s %s %f,%f" % tuple((mount_radius, mount_radius, 0, 0 if holes_count!=1 else 1, 1 ) + points[1]) +
					"L %f,%f" % points[2] +
					"A  %f,%f %s %s %s %f,%f" % tuple((r_outer, r_outer, 0, 0 if holes_count!=1 else 1, 0 ) + points[3]) +
					"Z"
					)

		# Draw mount hole
		# A : rx,ry  x-axis-rotation, large-arch-flag, sweepflag  x,y
		r = mount_hole/2
		path += (
				"M %f,%f" % (0,r) +
				"A  %f,%f %s %s %s %f,%f" % (r,r, 0,0,0, 0,-r) +
				"A  %f,%f %s %s %s %f,%f" % (r,r, 0,0,0, 0,r) 
				)
		
		# Embed gear in group to make animation easier:
		#  Translate group, Rotate path.
		t = 'translate(' + str( self.view_center[0] ) + ',' + str( self.view_center[1] ) + ')'
		g_attribs = {inkex.addNS('label','inkscape'):'Gear' + str( teeth ),
                                inkex.addNS('transform-center-x','inkscape'): str(-bbox_center[0]),
                                inkex.addNS('transform-center-y','inkscape'): str(-bbox_center[1]),
				'transform':t, 
				'info':'N:'+str(teeth)+'; Pitch:'+ str(pitch) + '; Pressure Angle: '+str(angle) }
		# add the group to the current layer
		g = inkex.etree.SubElement(self.current_layer, 'g', g_attribs )

		# Create SVG Path for gear
		style = { 'stroke': '#000000', 'fill': 'none' }
		gear_attribs = {'style':simplestyle.formatStyle(style), 'd':path }
		gear = inkex.etree.SubElement(g, inkex.addNS('path','svg'), gear_attribs )

		# Add center
		if centercross:
			style = { 'stroke': '#000000', 'fill': 'none', 'stroke-width':0.1 }
			cs = str(pitch/3) # centercross size
			d = 'M-'+cs+',0L'+cs+',0M0,-'+cs+'L0,'+cs  # 'M-10,0L10,0M0,-10L0,10'
			center_attribs = {inkex.addNS('label','inkscape'):'Center cross','style':simplestyle.formatStyle(style), 'd':d}
			center = inkex.etree.SubElement(g, inkex.addNS('path','svg'), center_attribs )

		# Add pitch circle (for mating)
		if pitchcircle:
			draw_SVG_circle(pitch_radius,0,0, 'none', 0.1, 'Pitch circle', g )

                # Add Annotation (above)
                if self.options.annotation:
                        notes =['Teeth: %d   Pitch: %2.4f' % (teeth, pitch),
                                'Pressure Angle: %2.4f' % (angle),
                                'Pitch diameter: %2.4f' % (pitch_diameter),
                                'Outer diameter: %2.4f' % (outer_diameter),
                                'Base diameter: %2.4f'  % (base_diameter),
                                'Addendum: %2.4f'  % (addendum),
                                'Dedendum: %2.4f'  % (dedendum)
                                ]
                        text_height = 22
                        # position above
                        y = - outer_radius - (len(notes)+1) * text_height * 1.2
                        for note in notes:
                                self.add_text(g, note, [0,y], text_height)
                                y += text_height * 1.2

                # Draw rack (below)
                if self.options.drawrack:
                        base_height = self.options.base_height * units
                        tab_width = self.options.base_tab * units
                        path = generate_rack_path(tooth_count, pitch, angle,
                                                  base_height, tab_width)
                        # position below Gear
                        t = 'translate(' + str( 0 ) + ',' + str( outer_radius + addendum*2) + ')'
                        g_attribs = {
                            inkex.addNS('label', 'inkscape'): 'RackGear' + str(tooth_count),
                            'transform': t}
                        rack = inkex.etree.SubElement(g, 'g', g_attribs)

                        # Create SVG Path for gear
                        style = {'stroke': '#000000', 'fill': 'none'}
                        gear_attribs = {
                            'style': simplestyle.formatStyle(style),
                            'd': path}
                        gear = inkex.etree.SubElement(
                            rack, inkex.addNS('path', 'svg'), gear_attribs)   

if __name__ == '__main__':
	e = Gears()
	e.affect()

# Notes

# add to center hole a D for a key (width, height defined on pg 737
##def generate_gear_path(teeth_count, module, pressure_angle, mount_hole_dia,
##                       clearance=0, unit_factor=1,
##                       mount_radius=0, spoke_count=0, spoke_border=0,
##                       accuracy=20, draw_guides=False,
##                       ):
##        """ returns a path (for svg) of the gear where:
##            - unit_factor is precomputed based on document and dialog dimension
##            - spoke_count equivalent to hole_count
##            - draw_guides shows both centercross and pitch circle.
##            Missing parameters:
##            - key - an (x,y) tuple of box shape to cut out of mount hole
##            - spoke_rounding - for smoother internal hole corners
##            - 
##        """
##        # Calls a function to calculate pitch circle (so can be called to show layout of simplified gears)
##        # - draw pitch circle using draw_SVG_circle()
##        pass
##
##def generate_rack_path(teeth_count, module, pressure_angle, tab_length,
##                       clearance=0, unit_factor=1,
##                       accuracy=20, draw_guides=False
##                      ):
##        """ Just draw the rack """
##        pass
### and perhaps: generate_ring_path
