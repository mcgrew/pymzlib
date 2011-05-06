#!/usr/bin/env python

import mzlib
from sys import argv


def main( options=None, args=None ):
	"""The main method"""
	if not len( args ):
		print ( "This program requires a filename argument" )
		sys.exit( 1 )
	inputFile = args[ 0 ]
	outputFile = args[ 1 ]
	dotPos = inputFile.rfind( '.' )
	if ( dotPos < 0 ): dotPos = None
	rawData = mzlib.RawData( inputFile )
	rawData.write( outputFile )
	
if __name__ == "__main__":
	main( args = argv[1:] )

