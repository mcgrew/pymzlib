#!/usr/bin/env python
"""

Copyright: 2010 Thomas McGrew

License: MIT license.

	Permission is hereby granted, free of charge, to any person
	obtaining a copy of this software and associated documentation
	files (the "Software"), to deal in the Software without
	restriction, including without limitation the rights to use,
	copy, modify, merge, publish, distribute, sublicense, and/or sell
	copies of the Software, and to permit persons to whom the
	Software is furnished to do so, subject to the following
	conditions:

	The above copyright notice and this permission notice shall be
	included in all copies or substantial portions of the Software.

	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
	EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
	OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
	NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
	HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
	WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
	FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
	OTHER DEALINGS IN THE SOFTWARE.


	Version beta 2011.05.26

"""

VERSION = "0.2-beta-2011.05.26"

import sys
import os
import os.path
#from hashlib import sha1
#import cPickle
from optparse import OptionParser,SUPPRESS_HELP
import numpy as numerical
import mzlib
from csv import DictReader
try:
	import filters
except ImportError:
	filters = None
try:
	import matplotlib
	from matplotlib.font_manager import FontProperties
except ImportError:
	sys.stderr.write( "\n*** THIS PROGRAM REQUIRES MATPLOTLIB, WHICH DOES NOT "
	                  "APPEAR TO BE INSTALLED ***\n" )
	raise 

# To do: 
# add an option to allow indexing by scan number

COLORS = {
	# Available colors (the lower case letter is used for that color):
	# rED, gREEN, bLUE, cYAN, mAGENTA, yELLOW, BLACk, wHITE	
	# html color codes can also be used.
	"intensity" : [ "b","r","y","c","m","g" ],
	"noise"     : [ "b","r","y","c","m","g" ],
	"ref"       : [ "k","c","m","y","r","g","b"]
}

def parseOpts( ):
	"""
	Parses the command line options passed into the program

	returns:
		2 element list ( opts, args ) 
	
	"""	
	optparser = OptionParser( version="%prog " + VERSION )

	optparser.add_option( "--minrt", type="float", default=0, 
	                      dest="minTime", metavar="RT", help="The minimum "
												"retention time to show on the graph" )

	optparser.add_option( "--maxrt", type="float", default=0, 
	                      dest="maxTime", metavar="RT", help="The maximum "
												"retention time to show on the graph" )

	optparser.add_option( "--bpc", action="store_true", default=False, dest="bpc",
	                      help="Show only base peaks, i.e. the highest intensity "
												"value at each retention time (BPC) instead of the "
												"total ion chromatogram (TIC)." )

	optparser.add_option( "-m", "--mass", type="float", dest="mass", 
	                      help="Filter data by a particular mass, a.k.a Selected "
												"Ion Chromatogram (SIC)" )
	
	optparser.add_option( "-w", "--mass-window", type="float", dest="massWindow",
	                      default=0.2, metavar="SIZE", help="The range of the "
												"mass to be displayed in Dalton. Default is %default. " 
											  "This option is only used with -m (SIC mode)" )
											 
	optparser.add_option( "-c", "--connect-peaks", action="store_true", 
	                       dest="connectPeaks", help="Draw lines connecting the "
												 "peaks from Xmass output" )

	optparser.add_option( "-l", "--legend", action="store_true", default=False, 
	                      dest="showLegend", help="Display a legend." )

	optparser.add_option( "--short-filename", action="store_true", default=False, 
	                      dest="shortFilename", help="Display only the filename "
												"(without the path) in the legend." )

	optparser.add_option( "--labels", action="store_true", dest="massLabels", 
	                     help="Show a label for each peak containing its mass" )

	optparser.add_option( "--hide-peaks", action="store_false", default=True, 
	                      dest="showPeaks", help="Do not show the peak bars from "
												"the xmass output on the graph" )

	optparser.add_option( "-n", "--noise", action="store_true", default=False, 
	                      dest="showNoise", help="Show the noise from the xmass "
												"output on the graph" )

	optparser.add_option( "--alpha", type="float", default=1, dest="markerAlpha", 
	                      metavar="ALPHA", help="Set the starting opacity level "
												"of the lines on the graph (0.0-1.0, Defaults to "
												"%default)" )

	optparser.add_option( "--line-width", type="float", default=1, 
	                      dest="lineWidth", metavar="WIDTH", help="Set the width "
												"of the bars on the graph. Defaults to %default" )

	optparser.add_option( "-s", "--script", action="store_true", 
	                      dest="scriptMode", help="Run in script mode, i.e. do "
												"not display the graph. This is only useful with the "
												"-o option" )

	optparser.add_option( "-v", "--verbose", action="count", dest="verbosity", 
	                      default=0, help="Print more messages about what the "
											  "program is doing." )

	optparser.add_option( "--subtract-noise", action="store_true", 
	                      dest="removeNoise", help="Subtract the noise from the "
												" intensity values in the peak list" )

	optparser.add_option( "-o", "--out", dest="outputFile", metavar="FILE",
	                      help="Save the generated graph to the given file. "
											  "Supported types depends on your platform, but most "
											  "platforms support png, pdf, ps, eps and svg." )

	optparser.add_option( "--width", type="int", default=800, dest="width",
	                      help="The width of the generated image. "
												"Defaults to %default. For use with -o" )

	optparser.add_option( "--height", type="int", default=450, dest="height",
	                      help="The height of the generated image. "
												"Defaults to %default. For use with -o" )

	optparser.add_option( "--dpi", type="int", default=72, dest="dpi",
	                      help="The dpi of the generated image. "
												"Defaults to %default. For use with -o" )

#	optparser.add_option( "--by-scan", action="store_true", dest="byScan",
#	                      help="Index the graph by scan number instead of retention time" )

	if filters:
		optparser.add_option( "--hpf", type="float", dest="hpfThreshold", 
		                      metavar="THRESHOLD", help="Run any chromatogram data "
													"through an fft high pass filter before displaying. "
													"hpfThreshold should be a value between 0 and 1" )

		optparser.add_option( "--lpf", type="float", dest="lpfThreshold", 
		                      metavar="THRESHOLD", help="Run any chromatogram data "
													"through an fft low pass filter before displaying. " 
													"lpfThreshold should be a value between 0 and 1" )

	optparser.add_option( "--snratio", type="float", default=0, 
	                      dest="filterLevel", metavar="RATIO", help="Drop peaks "
												"whose signal/noise ratio is less than RATIO" )

	return optparser.parse_args( )


def main( options=None, args=None ):
	"""The main method"""
	global COLORS

	if options.scriptMode:
		matplotlib.use( 'Agg' )
	import pylab

	thisFigure = pylab.figure( )

	if options.outputFile:
		thisFigure.set_size_inches(( 
		  float( options.width ) / options.dpi, 
			float( options.height ) / options.dpi ))

	pylab.subplots_adjust( left = 0.6 / options.width * options.dpi, 
	                       right = 1.0 - 0.2 / options.width * options.dpi, 
	                       top = 1.0 - 0.45 / options.height * options.dpi, 
												 bottom = 0.5 / options.height * options.dpi )
	barOffset = options.lineWidth / 2
	barAlpha = options.markerAlpha * 2 / 3


	rawFiles = [ ]
	rawTypes = [ '.csv', '.mzdata', '.mzxml', '.mzxml.xml', 
	             '.json', '.json.gz' ]
	for i in range( len( args )-1, -1, -1 ):
		arg = args[ i ]
		try:
			# check the extension to see if this is xmass input data
			for type_ in rawTypes:
				if arg.lower( ).endswith( type_ ):
					rawFiles.append( args.pop( i ))
					continue
		except ValueError:
			pass
		

	if rawFiles:
		for r in rawFiles:
			ref = mzlib.RawData( )
			if not ( ref.read( r )):
				sys.stderr.write( "Error: Unable to load data from '%s'" % r )
				exit( -1 )

			if options.shortFilename:
				filename = os.path.basename( r )
			else:
				filename = r

			# apply any filters
			if options.mass:
				ref.onlyMz( options.mass, options.massWindow )

			if options.maxTime or options.minTime:
				if options.maxTime:
					ref.onlyScans( options.minTime, options.maxTime )
				else:
					ref.onlyScans( options.minTime )

			rt = [ scan[ "retentionTime" ] for scan in ref if scan[ "msLevel" ] == 1 ]
			if options.bpc:
				yAxis = ref.bpc( 1 )
			else:
				yAxis = ref.tic( 1 )

			if filters:
				if options.lpfThreshold and options.hpfThreshold:
					yAxis = filters.bpf( yAxis, options.hpfThreshold, options.lpfThreshold )
				elif options.lpfThreshold:
					yAxis = filters.lpf( yAxis, options.lpfThreshold )
				elif options.hpfThreshold:
					yAxis = filters.hpf( yAxis, options.hpfThreshold )

			pylab.plot( rt, yAxis, COLORS['ref'][0] , alpha = options.markerAlpha,
			     linewidth=options.lineWidth,  
					 label = filename )
			COLORS['ref'] = COLORS['ref'][1:] + [ COLORS['ref'][0]]


	# The following section of code is specific to the OmicsDP data formats.
	# You can safely delete this section if you are using this software outside
	# of that environment.
  # BEGIN READING DLTs
	for arg in args:
		scan = numerical.empty( 0, numerical.uint64 ) # scan number
		barRt = numerical.empty( 0, numerical.float64 ) # retention time 
		barIntensity = numerical.empty( 0, numerical.float64 )
		barNoise = numerical.empty( 0, numerical.float64 )
		labels = [ ]
		try:
			f = open( arg )
			lines = DictReader( f )
		except IOError:
			sys.stderr.write("Error: unable to read file '%s'\n" % arg )
			exit( -1 )

		if options.shortFilename:
			filename = os.path.basename( arg )
		else:
			filename = arg

		for line in lines:
			try:
				scanValue = int( line[ 'Scan' ])
				rtValue = float( line[ 'RT(min)'] )
				mzValue = float( line[ 'M/Z' ] )
				noiseValue = float( line[ 'LC_Noise' ] )
				intValue = float( line[ 'Int' ] ) 
				if ( rtValue < options.minTime or 
					   ( options.maxTime and rtValue > options.maxTime )):
					continue
				if ((( not noiseValue ) or 
					     intValue/noiseValue < options.filterLevel ) or 
				       ( options.mass and 
							   abs( options.mass - mzValue ) > options.massWindow )):
					if options.verbosity:
						sys.stderr.write( "Dropping line %s" % ( line ))
					continue
				# using plot( ) produces a more responsive graph than vlines( )
				if len( scan ) and scanValue == scan[ -1 ]:
					if options.bpc:
						if intValue > barIntensity[ -2 ]:
							barIntensity[ -2 ] = intValue
							barNoise[ -2 ] = noiseValue
							labels[ -1 ] = "(%.2f," % ( mzValue - 0.005 ) #truncate, don't round
					else:
						barIntensity[ -2 ] += intValue
						barNoise[ -2 ] += noiseValue
						labels[ -1 ] += " %.2f," % ( mzValue - 0.005 ) #truncate, don't round
				else:
					# appending [0, value, 0] allows us to plot a bar graph using lines
					barRt = numerical.append( barRt, [ rtValue, rtValue, rtValue ])
					barIntensity = numerical.append( barIntensity, [ 0, intValue, 0 ])
					barNoise = numerical.append( barNoise, [ 0, noiseValue, 0 ])
					scan = numerical.append( scan, scanValue )
					if ( len( labels )):
						labels[ -1 ] = labels[ -1 ][ :-1 ] + ')' # replace the last , with )
					labels.append(  "(%.2f," % ( mzValue - 0.005 )) #truncate, don't round



			except ( ValueError, IndexError ):
				if options.verbosity:
					sys.stderr.write( "Skipping line %s" % ( line ))

			if ( len( labels )):
				labels[ -1 ] = labels[ -1 ][ :-1 ] + ')' # replace the last , with )

		if options.massLabels:
			for i in xrange( len( labels )):
				pylab.annotate( labels[ i ], ( barRt[ 3 * i + 1 ], barIntensity[ 3 * i + 1 ]),
				          size=9)

		# calculate alpha based on which file this is in the list
		alpha = ( options.markerAlpha - options.markerAlpha * 
		          ( args.index( arg ) / float( len( args ))) * 0.75 )

		if options.showPeaks:
			if not options.removeNoise:
				barIntensity += barNoise
			pylab.plot( barRt, barIntensity, COLORS['intensity'][0] , 
			      linewidth = options.lineWidth*2, alpha = alpha, 
						label = ( "%s - intensity (%d peaks)" % 
						( filename, len( barIntensity )/3)))

		if options.connectPeaks:
			pylab.plot( barRt[ 2::3 ], barIntensity[ 1::3 ], COLORS['intensity'][0], 
			      alpha = alpha, linewidth=options.lineWidth  )
		COLORS['intensity'] = COLORS['intensity'][1:] + [ COLORS['intensity'][0]]
				
		if options.showNoise:
			pylab.plot( barRt[ 2::3 ], barNoise[ 1::3 ], COLORS['noise'][0], alpha = alpha, 
			      linewidth=options.lineWidth, 
			      label = ( "%s - noise (%d points)" % ( filename, len( barNoise )/3)))
			COLORS['noise'] = COLORS['noise'][1:] + [ COLORS['noise'][0]]
		if len( barRt ):
			#draw a horizontal black line at 0
			pylab.plot( [barRt[1], barRt[-2]], [0,0], 'k', linewidth=options.lineWidth )

		f.close( )
		# END READING DLTs

	if options.showLegend:
		legend = pylab.legend( loc="upper left", prop=FontProperties( size='small' ))

	pylab.grid( )
	axes = thisFigure.get_axes( )[ 0 ]
	axes.set_xlabel( "Time (min)" )
	axes.set_ylabel( "Intensity" )
	axes.ticklabel_format( style="scientific", axis="y", scilimits=(3,3) )

	if not len( rawFiles ):
		if ( options.bpc ):
			axes.set_title( "Base Peaks" )
		else:
			axes.set_title( "Peaks" )
	elif options.bpc:
		if options.mass:
			axes.set_title( 
				"Selected Base Peak Chromatogram (M/Z: %f, Tolerance: %f)" % 
				( options.mass, options.massWindow ))
		else:
			axes.set_title( "Base Peak Chromatogram" )
	else:
		if options.mass:
			axes.set_title( 
				"Selected Ion Chromatogram (M/Z: %f, Tolerance: %f)" %
				( options.mass, options.massWindow ))
		else:
			axes.set_title( "Total Ion Chromatogram" )
	if options.outputFile:
		thisFigure.savefig( options.outputFile, dpi=options.dpi )
	if not options.scriptMode:
		pylab.show( )
## end main( )
	
if ( __name__ == "__main__" ):
	main( *parseOpts( ))

