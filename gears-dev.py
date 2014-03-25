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

__version__ = '0.5'

def linspace(a,b,n):
    """ return list of linear interp of a to b in n steps
        - if a and b are ints - you'll get an int result.
        - n must be an integer
    """
    return [a+x*(b-a)/(n-1) for x in range(0,n)]

def involute_intersect_angle(Rb, R):
    Rb, R = float(Rb), float(R)
    return (sqrt(R**2 - Rb**2) / (Rb)) - (acos(Rb / R))

def point_on_circle(radius, angle):
    " return xy coord of the point at distance radius from origin at angle "
    x = radius * cos(angle)
    y = radius * sin(angle)
    return (x, y)

def points_to_bbox(p):
    """ from a list of points (x,y pairs)
        - return the lower-left xy and upper-right xy
    """
    llx = urx = p[0][0]
    lly = ury = p[0][1]
    for x in p[1:]:
        if   x[0] < llx: llx = x[0]
        elif x[0] > urx: urx = x[0]
        if   x[1] < lly: lly = x[1]
        elif x[1] > ury: ury = x[1]
    return (llx, lly, urx, ury)

def points_to_bbox_center(p):
    """ from a list of points (x,y pairs)
        - find midpoint of bounding box around all points
        - return (x,y)
    """
    bbox = points_to_bbox(p)
    return ((bbox[0]+bbox[2])/2.0, (bbox[1]+bbox[3])/2.0)
                
def points_to_svgd(p):
    " convert list of points into a closed SVG path list"
    f = p[0]
    p = p[1:]
    svgd = 'M%.4f,%.4f' % f
    for x in p:
        svgd += 'L%.4f,%.4f' % x
    svgd += 'z'
    return svgd

def draw_SVG_circle(parent, r, cx, cy, name, style):
    " add an SVG circle entity to parent "
    circ_attribs = {'style': simplestyle.formatStyle(style),
                    'cx': str(cx), 'cy': str(cy), 
                    'r': str(r),
                    inkex.addNS('label','inkscape'):name}
    circle = inkex.etree.SubElement(parent, inkex.addNS('circle','svg'), circ_attribs )


def gear_calculations(num_teeth, metric, module, circular_pitch, pressure_angle, clearance):
    """ intention is to put base calcs for gear in one place.
        - does not calc for stub teeth just regular
        - pulled from web - might not be the right core list for this program
    """
    if metric:
        # have unneccssary duplicates for inch/metric
        #  probably only one needs to be calculated.
        #  I.e. calc module and derive rest from there.
        #  or calc dp
        diametral_pitch = 25.4 / module # dp in inches
        pitch_diameter = module * num_teeth
        addendum = module
        #dedendum = 1.157 * module # what is 1.157 ?? a clearance calc ?
        dedendum = module + clearance # or maybe ?? max(module + clearance, 1.157 * module)
        working_depth = 2 * module
        whole_depth = 2.157 * module
        outside_diameter = module * (num_teeth + 2)
    else:
        diametral_pitch = pi / circular_pitch
        pitch_diameter = num_teeth / diametral_pitch
        addendum = 1 / diametral_pitch
        dedendum = 1.157 / diametral_pitch # ?? number from ?
        working_depth = 2 / diametral_pitch
        whole_depth = 2.157 / diametral_pitch
        outside_diameter = (teeth + 2) / diametral_pitch
    #
    base_diameter = pitch_diameter * cos(pressure_angle)
    #
    return (diametral_pitch, pitch_diameter, addendum, dedendum,
            working_depth, whole_depth, outside_diameter, base_diameter)

 

def generate_rack_path(tooth_count, tooth_width, pressure_angle,
                       base_height, tab_length, clearance=0, draw_guides=False):
        """ Return path (suitable for svg) of the Rack gear.
            - rack gear uses straight sides
                - involute on a circle of infinite radius is a simple linear ramp
            - needs adj for clearance
            - needs to draw pitch circle line
        """
        spacing = tooth_width # basically right...?
        x = -tooth_count * spacing - tab_length # center rack in drawing
        tas = tan(radians(pressure_angle)) * spacing
        #inkex.debug("angle=%s spacing=%s"%(pressure_angle, spacing))
        # Start with base tab on LHS
        points = [] # make list of points
        points.append((x, base_height))
        points.append((x, 0))
        x += tab_length
        points.append((x, 0))
        # An involute on a circle of infinite radius is a simple linear ramp.
        # We need to add curve at bottom and use clearance.
        for i in range(tooth_count):
            # move along path, generating the next 'tooth'
            points.append((x, 0))
            points.append((x + tas, -spacing - clearance))
            points.append((x + spacing, -spacing - clearance)) # just guessing - probably should be clearance + addendum
            points.append((x + spacing + tas, 0))
            x += spacing * 2.0
        x -= spacing - tas # remove last adjustment
        # add base on RHS
        points.append((x, 0))
        x += tab_length
        points.append((x, 0))
        points.append((x, base_height)) # add end tab
        # Draw line representing the pitch circle
        if draw_guides:
            # not sure where pitch circle is
            pass
        # return points ready for use in an SVG 'path'
        return points_to_svgd(points)


class Gears(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        # try using inkex.debug(string) instead...
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
                                     action="store", type="string",
                                     dest="units", default='mm',
                                     help="Units this dialog is using")

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

        self.OptionParser.add_option("", "--spoke-count",
                                     action="store", type="int",
                                     dest="spoke_count", default=3,
                                     help="Spokes count")

        self.OptionParser.add_option("", "--spoke-width",
                                     action="store", type="float",
                                     dest="spoke_width", default=5,
                                     help="Spoke width")

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
        """ Create and insert a single line of text into the svg under node.
            - use 'text' type and label as anootation
            - where color is Ponoko Orange - so ignored when lasercutting
        """
        line_style = {'font-size': '%dpx' % text_height, 'font-style':'normal', 'font-weight': 'normal',
                     'fill': '#F6921E', 'font-family': 'Bitstream Vera Sans,sans-serif',
                     'text-anchor': 'middle', 'text-align': 'center'}
        line_attribs = {inkex.addNS('label','inkscape'): 'Annotation',
                       'style': simplestyle.formatStyle(line_style),
                       'x': str(position[0]),
                       'y': str((position[1] + text_height) * 1.2)
                       }
        line = inkex.etree.SubElement(node, inkex.addNS('text','svg'), line_attribs)
        line.text = text

           
    def calc_units_factor(self, this_units):
        """ given the document units and units declared in this extension's dialog
            - return the scale factor for all dimension conversions
        """
        namedView = self.document.getroot().find(inkex.addNS('namedview', 'sodipodi'))
        doc_units = inkex.uutounit(1.0, namedView.get(inkex.addNS('document-units', 'inkscape')))
        dialog_units = inkex.uutounit(1.0, this_units)
        #inkex.debug("docunits = %s dialog units = %s factor = %s" % (doc_units, dialog_units, doc_units/dialog_units))
        return (doc_units/dialog_units)
        

    def effect(self):
        """ Calculate Gear factors from inputs.
            - Make list of radii, angles, and centers for each tooth and iterate through them
            - Turn on other visual features e.g. cross, rack, annotations, etc
        """
        path_stroke = '#000000'  # might expose one day
        path_fill   = 'none'     # no fill - just a line
        path_stroke_width  = 0.6 # might expose one day (guides are /5 thick)
        
        # Debug using:  inkex.debug( "angle=%s pitch=%s" % (angle, pitch) )
        # take into account document dimensions and units in dialog. - calc factor
        unit_factor = self.calc_units_factor(self.options.units)
        teeth = self.options.teeth
        angle = self.options.angle # Angle of tangent to tooth at circular pitch wrt radial line.
        # Clearance: Radial distance between top of tooth on one gear to bottom of gap on another.
        clearance = self.options.clearance * unit_factor
        
        accuracy_involute = 20 # Number of points of the involute curve
        accuracy_circular = 9  # Number of points on circular parts
        if self.options.accuracy is not None:
            if self.options.accuracy == 0:  
                # automatic
                if   teeth < 10: accuracy_involute = 20
                elif teeth < 30: accuracy_involute = 12
                else:            accuracy_involute = 6
            else:
                accuracy_involute = self.options.accuracy
            accuracy_circular = min(3, int(self.options.accuracy) / 2 - 1) # never less than three
##            if accuracy_circular < 3: accuracy_circular = 3
##            # replaced following by doing unit_factor above
##            if units == 0.0:
##                if use_metric_module:
##                    units = 3.5433070866 # ?? this is doing direct 90dpi adjustment
##                else:
##                    units = 1
            #
            use_metric_module = self.options.metric_or_pitch == 'useMetric'
            if use_metric_module:
            # options.pitch is metric modules, we need circular pitch
                pitch = self.options.module * unit_factor * pi
            else:
                #pitch = inkex.uutounit(self.options.pitch,'in') * unit_factor # wrong!
                pitch = self.options.pitch * unit_factor # wrong! (see first annotation - compare values with real table)
        
        mount_hole = self.options.mount_hole * unit_factor
        mount_radius = self.options.mount_radius * unit_factor

        spoke_count = self.options.spoke_count
        holes_rounding = self.options.holes_rounding * unit_factor
        spoke_width = self.options.spoke_width * unit_factor
        
        # should we combine to draw_guides ?
        centercross = self.options.centercross # draw center or not (boolean)
        pitchcircle = self.options.pitchcircle # draw pitch circle or not (boolean)
        
        # print >>sys.stderr, "Teeth: %s\n"     % teeth
        two_pi = 2.0 * pi

        # Hopefully replace a lot of these with a call to a modified gear_calculations() above
        
        # Pitch (circular pitch): Length of the arc from one tooth to the next)
        # Pitch diameter: Diameter of pitch circle.
        pitch_diameter = teeth * pitch / pi
        pitch_radius   = pitch_diameter / 2.0

        # Base Circle
        base_diameter = pitch_diameter * cos( radians( angle ) )
        base_radius   = base_diameter / 2.0

        # Diametrial pitch: Number of teeth per unit length.
        pitch_diametrial = teeth / pitch_diameter

        # Addendum: Radial distance from pitch circle to outside circle.
        addendum = 1.0 / pitch_diametrial

        # Outer Circle
        outer_radius = pitch_radius + addendum
        outer_diameter = outer_radius * 2.0

        # Tooth thickness: Tooth width along pitch circle.
        tooth  = ( pi * pitch_diameter ) / ( 2.0 * teeth )

        # Undercut?
        undercut = (2.0 / ( sin( radians( angle ) ) ** 2))
        needs_undercut = teeth < undercut

        # Dedendum: Radial distance from pitch circle to root diameter.
        dedendum = addendum + clearance

        # Root diameter: Diameter of bottom of tooth spaces. 
        root_radius =  pitch_radius - dedendum
        root_diameter = root_radius * 2.0

        # All base calcs done. Start building gear
        
        half_thick_angle = two_pi / (4.0 * teeth ) #?? = pi / (2.0 * teeth)
        pitch_to_base_angle  = involute_intersect_angle( base_radius, pitch_radius )
        pitch_to_outer_angle = involute_intersect_angle( base_radius, outer_radius ) - pitch_to_base_angle

        start_involute_radius = max(base_radius, root_radius)
        radii = linspace(start_involute_radius, outer_radius, accuracy_involute)
        angles = [involute_intersect_angle(base_radius, r) for r in radii]

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

            points_on_outer_radius = [ point_on_circle(outer_radius, x) for x in linspace(offsetangles1[-1], offsetangles2[-1], accuracy_circular) ]

            if root_radius > base_radius:
                pitch_to_root_angle = pitch_to_base_angle - involute_intersect_angle(base_radius, root_radius )
                root1 = pitch1 - pitch_to_root_angle
                root2 = pitch2 + pitch_to_root_angle
                points_on_root = [point_on_circle (root_radius, x) for x in linspace(root2, root1+(two_pi/float(teeth)), accuracy_circular) ]
                p_tmp = points1 + points_on_outer_radius[1:-1] + points2[::-1] + points_on_root[1:-1] # [::-1] reverses list; [1:-1] removes first and last element
            else:
                points_on_root = [point_on_circle (root_radius, x) for x in linspace(base2, base1+(two_pi/float(teeth)), accuracy_circular) ]
                p_tmp = points1 + points_on_outer_radius[1:-1] + points2[::-1] + points_on_root # [::-1] reverses list

            points.extend( p_tmp )

        path = points_to_svgd( points )
        bbox_center = points_to_bbox_center( points )
        # print >>self.tty, bbox_center

        # Holes
        holes = ''
        r_outer = root_radius - spoke_width
        for i in range(spoke_count):
            points = []
            start_a, end_a = i * two_pi / spoke_count, (i+1) * two_pi / spoke_count
            # inner circle around mount
            # - a better way to do this might be to increase local spoke width to be larger by epsilon than mount radius
            # - this soln prevents blowout but does not make a useful result.
            # Also mount radius should increase to avoid folding over when spoke_width gets big. But by what factor ?
            # - can we calc when spoke_count*(spoke_width+delta) exceeds circumference of mount_radius circle.
            # - then increase radius to fit - then recalc mount_radius.
            asin_factor = spoke_width/mount_radius/2
            # check if need to clamp radius
            if asin_factor > 1 : asin_factor = 1
            #a = asin(spoke_width/mount_radius/2)
            a = asin(asin_factor)
            points += [ point_on_circle(mount_radius, start_a + a), point_on_circle(mount_radius, end_a - a)]
            # outer circle near gear
            
##            try:
##                a = asin(spoke_width/r_outer/2)
##            except:
##                print >> sys.stderr, "error: Spoke width is too large:", spoke_width/unit_factor, "max=", r_outer*2/unit_factor
            
            # a better way to do this might be to decrease local spoke width to be smaller by epsilon than r_outer
            # this soln prevents blowout but does not make a useful result. (see above)
            asin_factor = spoke_width/r_outer/2
            # check if need to clamp radius
            if asin_factor > 1 : asin_factor = 1
            a = asin(asin_factor)
            points += [point_on_circle(r_outer, end_a - a), point_on_circle(r_outer, start_a + a) ]

            path += (
                    "M %f,%f" % points[0] +
                    "A  %f,%f %s %s %s %f,%f" % tuple((mount_radius, mount_radius, 0, 0 if spoke_count!=1 else 1, 1 ) + points[1]) +
                    "L %f,%f" % points[2] +
                    "A  %f,%f %s %s %s %f,%f" % tuple((r_outer, r_outer, 0, 0 if spoke_count!=1 else 1, 0 ) + points[3]) +
                    "Z"
                    )

        # Draw mount hole
        # A : rx,ry  x-axis-rotation, large-arch-flag, sweepflag  x,y
        r = mount_hole / 2
        path += (
                "M %f,%f" % (0,r) +
                "A  %f,%f %s %s %s %f,%f" % (r,r, 0,0,0, 0,-r) +
                "A  %f,%f %s %s %s %f,%f" % (r,r, 0,0,0, 0,r) 
                )
        
        # Embed gear in group to make animation easier:
        #  Translate group, Rotate path.
        t = 'translate(' + str( self.view_center[0] ) + ',' + str( self.view_center[1] ) + ')'
        g_attribs = { inkex.addNS('label','inkscape'):'Gear' + str( teeth ),
                      inkex.addNS('transform-center-x','inkscape'): str(-bbox_center[0]),
                      inkex.addNS('transform-center-y','inkscape'): str(-bbox_center[1]),
                      'transform':t,
                      'info':'N:'+str(teeth)+'; Pitch:'+ str(pitch) + '; Pressure Angle: '+str(angle) }
        # add the group to the current layer
        g = inkex.etree.SubElement(self.current_layer, 'g', g_attribs )

        # Create SVG Path for gear under top level group
        style = { 'stroke': path_stroke, 'fill': path_fill, 'stroke-width': path_stroke_width }
        gear_attribs = { 'style': simplestyle.formatStyle(style), 'd': path }
        gear = inkex.etree.SubElement(g, inkex.addNS('path','svg'), gear_attribs )

        # Add center
        if centercross:
            style = { 'stroke': path_stroke, 'fill': path_fill, 'stroke-width': path_stroke_width / 5.0 }
            cs = str(pitch / 3) # centercross length
            d = 'M-'+cs+',0L'+cs+',0M0,-'+cs+'L0,'+cs  # 'M-10,0L10,0M0,-10L0,10'
            center_attribs = { inkex.addNS('label','inkscape'): 'Center cross',
                               'style': simplestyle.formatStyle(style), 'd': d }
            center = inkex.etree.SubElement(g, inkex.addNS('path','svg'), center_attribs )

        # Add pitch circle (for mating)
        if pitchcircle:
            style = { 'stroke': path_stroke, 'fill': path_fill, 'stroke-width': path_stroke_width / 5.0 }
            draw_SVG_circle(g, pitch_radius, 0, 0, 'Pitch circle', style)

        # Add Rack (below)
        if self.options.drawrack:
            base_height = self.options.base_height * unit_factor
            tab_width = self.options.base_tab * unit_factor
            tooth_count = self.options.teeth_length
            path = generate_rack_path(tooth_count, tooth, angle,
                                      base_height, tab_width, clearance, pitchcircle)
            # position below Gear
            t = 'translate(' + str( 0 ) + ',' + str( outer_radius + (addendum + clearance)*2) + ')'
            g_attribs = { inkex.addNS('label', 'inkscape'): 'RackGear' + str(tooth_count),
                          'transform': t }
            rack = inkex.etree.SubElement(g, 'g', g_attribs)

            # Create SVG Path for gear
            style = {'stroke': path_stroke, 'fill': 'none', 'stroke-width': path_stroke_width}
            gear_attribs = { 'style': simplestyle.formatStyle(style),
                             'd': path }
            gear = inkex.etree.SubElement(
                rack, inkex.addNS('path', 'svg'), gear_attribs)

        # Add Annotations (above)
        if self.options.annotation:
            notes =['Document (%s) scale conversion = %2.4f' % (self.document.getroot().find(inkex.addNS('namedview', 'sodipodi')).get(inkex.addNS('document-units', 'inkscape')),
                                                                unit_factor),
                    'Teeth: %d   Pitch: %2.4f' % (teeth, pitch),
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

if __name__ == '__main__':
    e = Gears()
    e.affect()

# Notes

