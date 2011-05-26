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
import cgi 
import sys
import os
import re
from base64 import b64encode
try:
	from hashlib import sha1
except ImportError:
	from sha import sha as sha1
import cgitb; cgitb.enable( )

# local imports
os.environ[ 'HOME' ] = "/tmp"
import mzplot

DATA_ROOT = "/var/mzplot"
CACHE_DIR = "/tmp/mzplot"

class Options( object ):
	def __init__( self ):
		self.minTime       = 0
		self.maxTime       = 0
		self.bpc           = False
		self.mass          = 0
		self.massWindow    = 0.2
		self.connectPeaks  = False
		self.showLegend    = True
		self.shortFilename = True
		self.massLabels    = False
		self.showPeaks     = True
		self.showNoise     = False
		self.markerAlpha   = 1
		self.lineWidth     = 1
		self.scriptMode    = True
		self.verbosity     = 0
		self.removeNoise   = False
		self.outputFile    = None
		self.width         = 800
		self.height        = 450
		self.dpi           = 72
		self.filterLevel   = 0

	def hash( self ):
		optHash = sha1( )
		optHash.update( str( self.__dict__ ))
		return optHash.digest( )


def main( ):
	options = Options( )
	form = cgi.FieldStorage( )
	for i in form.keys( ):
		if not i == "files":
			value = None
			try: 
				value = float( form[ i ].value )
			except ValueError:
				if form[ i ].value.lower( ) == "true":
					value = True
				elif form[ i ].value.lower( ) == "false":
					value = False
			if ( value ):
				options.__setattr__( i, value )

	files = []
	if form.has_key( 'files' ):
		for file_ in re.split( "[,|]", form[ 'files' ].value ):
			if ( "../" in file_ ):
				print "Content-Type: text/plain"
				print
				print "Invalid path: " + file_
				return
			files.append( DATA_ROOT + "/" + file_ )

	if not os.path.exists( CACHE_DIR ):
		os.makedirs( CACHE_DIR )

	fileHash = sha1( )
	fileHash.update( str( sorted( files )))
	options.outputFile = ( CACHE_DIR + "/" + 
	  b64encode( options.hash( ) + fileHash.digest( ), "_.") + 
	  ".png" ).replace( "=", "" )
		
	if not os.path.exists( options.outputFile ):
		mzplot.main( options, files )

	# headers
	print "Content-Type: image/png"
	imageData = open( options.outputFile, 'r' )
	imageBytes = imageData.read( )
	imageData.close( )
	print "Content-Length: %d" % len( imageBytes )
	# arbitrary expiration date way in the future
	# essentially "cache this as long as you want."
#	print "Expires: Sun, 31 Dec 2006 16:00:00 GMT"
	print "Expires: Sun, 31 Dec 2034 16:00:00 GMT"
	print
	# end headers
	sys.stdout.write( imageBytes )

# run the main method if this file isn't being imported.
if ( __name__ == "__main__" ):
	main( )

