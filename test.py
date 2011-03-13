#!/usr/bin/env python2

from mzparse import Parser

parser = Parser( )
mzXML2 = parser.read( "testData/tiny1.mzXML2.0.mzXML" )
mzXML3 = parser.read( "testData/tiny1.mzXML3.0.mzXML" )
mzData = parser.readMzData( "testData/tiny1.mzData1.05.xml" )

if __name__ == "__main__":
#	print( mzXML3['scans'][0]['data'] )
#	print( mzXML3['scans'][1]['data'] )
	print( mzXML2['scans'][1]['data'] == mzXML3['scans'][1]['data'] )
	print( mzXML2['scans'][1]['data'] == mzData['scans'][1]['data'] )



