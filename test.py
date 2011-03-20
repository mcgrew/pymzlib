#!/usr/bin/env python2

from mzlib import *

mzXML2 = RawData( "testData/tiny1.mzXML2.0.mzXML" )
mzXML3 = RawData( "testData/tiny1.mzXML3.0.mzXML" )
mzData = RawData( "testData/tiny1.mzData1.05.xml" )
json   = RawData( "testData/tiny1.json" )
jsonGz = RawData( "testData/tiny1.json.gz" )

if __name__ == "__main__":
	print( "mzXML2.getScan( 5.89 )['points'] == mzXML3.getScan( 5.89 )['points']): " +
		str(mzXML2.getScan( 5.89 )['points'] == mzXML3.getScan( 5.89 )['points']))
	print( "mzXML2.getScan( 5.89 )['points'] == mzData.getScan( 5.89 )['points']): " +
		str(mzXML2.getScan( 5.89 )['points'] == mzData.getScan( 5.89 )['points']))
	print( "mzXML2[:] == mzXML3[:]: " + str(mzXML2[:] == mzXML3[:]))
	print( "mzXML2[:] == mzData[:]: " + str(mzXML2[:] == mzData[:]))
	print( "mzXML2[:] == json[:]  : " + str(mzXML2[:] == json[:]  ))
	print( "mzXML2[:] == jsonGz[:]: " + str(mzXML2[:] == jsonGz[:]))



