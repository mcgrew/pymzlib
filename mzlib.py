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


	Version alpha 2010.11.17

"""
import sys
import os
from xml.dom.minidom import parse
import struct
from base64 import b64decode
import types
import re
import zlib
import json
from copy import deepcopy

class RawData( object ):

	def __init__( self, _input=None ):
		if _input:
			if type( _input ) == RawData:
				# copy the passed in object
				self.data = deepcopy( _input.data )

			elif type( _input ) == str:
				# read the passed in file name
				self.read( _input )

		else:
			self.data = { 'scans' : [] }

	def getData( self ):
		return self.data

	def getScan( self, retentionTime ):
		"""
		Gets a scan from the data by retention time.
		:Parameters:
			retentionTime : float
				A float indicating the retention time of the scan to retrieve. The scan
				closest to that time is returned.

		rtype: dict
		return: A dict containing the scan points & metadata
		"""
		difference = 1048576
		returnvalue = None
		for scan in self.data[ 'scans' ]:
			currentDifference = scan[ 'retentionTime' ] - retentionTime
			if currentDifference < difference:
				difference = currentDifference
				returnvalue = scan
		return returnvalue
		
	def __getitem__( self, value ):	
		"""
		Returns a list indicating the sic intensity for each scan in order. Only for
		level 1 scans - other scans are omitted.
		:Parameters:
			value : slice
				The m/z indices to retrieve intensity values between.

		rtype: list
		return: A list of intensity values.
		"""
		returnvalue = []
		if type( value ) == slice:
			start = value.start if value.start else 0
			stop = value.stop if value.stop else 1048576
			
			for scan in self.data[ 'scans' ]:
				if scan['msLevel'] == 1:
					returnvalue.append( sum([ x[1] for x in scan[ 'points' ] 
														  if x[0] > start and x[0] < stop ]))
		else:
			for scan in self.data[ 'scans' ]:
				if scan['msLevel'] == 1:
					returnvalue.append( sum([ x[1] for x in scan[ 'points' ] 
															if x[0] == value ]))
		return returnvalue

	def __iter__( self ):
		return iter( self.data['scans'] )


	def read( self, filename ):
		"""
		Load a file into this reference. This method will automatically detect the
		file type based on the file extension.

		:Parameters:
			filename : str
				The name of the file to load.

		"""
	
		if not os.path.exists( filename ):
			raise IOError( "The file %s does not exist or is not readable" % filename )

		try:
			fileExt = filename[ filename.rindex( '.' )+1: ]
		except ValueError:
			return False

		if ( fileExt.lower( ) == "csv" ):
			return self.readCsv( filename )

		elif ( fileExt.lower( ) == "mzdata" ):
			return self.readMzData( filename )

		elif ( fileExt.lower( ) == "mzxml" ):
			return self.readMzXml( filename )
		else:
			sys.stderr.write( "Unrecognized file type for %s\n" % filename )
			return False

	def readCsv( self, filename ):
		"""
		Read a file in Agilent csv format. 

		:Parameters:
			filename : str
				The name of the file to load.

		"""
		self.data = { "scans" : [] }
		try:
			f = open( filename )
			lines = f.readlines( )
			f.close
		except IOError:
			sys.stderr.write( "Error: unable to read file '%s'\n" % filename )
			return False

		i = 0
		while( i < len( lines ) and lines[ i ][ :10 ] != "file name," ):
			i+= 1
		self.data[ 'sourceFile' ] = lines[ i ].split( ',' )[ 1 ]
		while ( i < len( lines ) and lines[ i ][ :9 ] != "[spectra]" ):
			i+=1
		i+=1

		if ( i > len( lines ) ):
			sys.stderr.write( "Unable to parse the reference file '%s'\n" % filename ) 
			return False

		scanId = 0
		for line in lines[ i: ]:
			scanId += 1
			values = line.split( ',' )
			if values[ 4 ] == '-':
				polarity = -1
			else:
				polarity = 1
			rt = float( values[ 0 ])
			count = float( values[ 6 ])
			intensityValues = [  float( x )  for x in values[ 8:-1:2 ] ]
			massValues = [ float( y ) for y in values[ 7:-1:2 ] ]

			self.data[ "scans" ].append({ 
				"retentionTime" : rt,
				"polarity" : polarity, 
				"msLevel" : 1,
				"id" : scanId,
				"lowMz" : min( massValues ),
				"highMz" : max( massValues ),
				"parentScan" : None,
				"precursorMz" : None,
				"collisionEnergy" : None,
				"points" : list( zip( massValues, intensityValues ))
			})
		return True

	def readMzData( self, filename ):
		"""
		Read a file in mzData format. 

		:Parameters:
			filename : str
				The name of the file to load.

		"""
		self.data = { "scans" : [] }
		dataFile = parse( filename )
		sourceFileNode = dataFile.getElementsByTagName( 'sourceFile' )[ 0 ].\
			getElementsByTagName( 'nameOfFile' )[ 0 ]
		self.data[ 'sourceFile' ] = re.sub( "<.*?>", "", sourceFileNode.toxml( ))
		scans = dataFile.getElementsByTagName( 'spectrum' )

		for scan in scans:
			parentScan = None
			precursorMz = None
			collisionEnergy = None
			scanId = int( scan.getAttribute( 'id' ))
			spectrumInstrument = scan.getElementsByTagName( 'spectrumInstrument' )[ 0 ]
			msLevel = int( spectrumInstrument.getAttribute( 'msLevel' ))
			lowMz = float( spectrumInstrument.getAttribute( 'mzRangeStart' ))
			highMz = float( spectrumInstrument.getAttribute( 'mzRangeStop' ))
			params = spectrumInstrument.getElementsByTagName( 'cvParam' )
			for param in params:
				if param.getAttribute( 'name' ) == 'Polarity':
					if param.getAttribute( 'value' ) == 'positive':
						polarity = 1
					else:
						polarity = -1
				if param.getAttribute( 'name' ) == 'TimeInMinutes':
					rt = float( param.getAttribute( 'value' ))

			
			massValues = self._unpackMzData( 
				scan.getElementsByTagName( 'mzArrayBinary' )[ 0 ].getElementsByTagName( 'data' )[ 0 ])
			intensityValues = self._unpackMzData( 
				scan.getElementsByTagName( 'intenArrayBinary' )[ 0 ].getElementsByTagName( 'data' )[ 0 ])

			precursors = scan.getElementsByTagName( 'precursor' )
			for precursor in precursors[ 0:1 ]:
				parentScan = int( precursor.getAttribute( 'spectrumRef' ))
				cvParams = precursor.getElementsByTagName( 'cvParam' )
				for param in cvParams:
					if param.getAttribute( 'name' ) == 'MassToChargeRatio':
						precursorMz = float( param.getAttribute( 'value' ))
#					if param.getAttribute( 'name' ) == 'ChargeState':
#						chargeState = int( param.getAttribute( 'value' ))
					if param.getAttribute( 'name' ) == 'CollisionEnergy':
						collisionEnergy = float( param.getAttribute( 'value' ))



			self.data[ "scans" ].append({ 
				"retentionTime" : rt,
				"polarity" : polarity, 
				"msLevel" : msLevel, 
				"id" : scanId,
				"lowMz" : lowMz,
				"highMz" : highMz,
				"parentScan" : parentScan,
				"precursorMz" : precursorMz,
				"collisionEnergy" : collisionEnergy,
				"points" : list( zip( massValues, intensityValues ))
			})

		return True


	def _unpackMzData( self, dataNode ):
		"""
		Internal function. Unpacks the scan data contained in a <data> node in mzdata 
		format.

		:Parameters:
			dataNode : xmlNode
				The xml node containing the scan data to be unpacked.

		"""
		scanSize = int( dataNode.getAttribute( 'length' ))
		if dataNode.getAttribute( 'endian' ) == 'little':
			byteOrder = '<'
		else:
			byteOrder = '>'
		if dataNode.getAttribute( 'precision' ) == '64':
			dataType = 'd'
		else: 
			dataType = 'f'

		return struct.unpack( byteOrder + ( dataType * scanSize ), 
			b64decode( re.sub( "<.*?>", "", dataNode.toxml( ))))

	def readMzXml( self, filename ):
		"""
		Read a file in mzXML format.

		:Parameters:
			filename : str
				The name of the file to load.

		"""
		self.data = { "scans" : [] }
		dataFile = parse( filename )
		scans = dataFile.getElementsByTagName( 'scan' )
		for scan in scans:
			collisionEnergy = None
			precursorMz = None
			msLevel = int( scan.getAttribute( "msLevel" ))
			scanSize = int( scan.getAttribute( 'peaksCount' ))
			rt = float( scan.getAttribute( 'retentionTime' )[ 2:-1 ] ) / 60
			scanId = int( scan.getAttribute( 'num' ))
			lowMz = float( scan.getAttribute( 'lowMz' ))
			highMz = float( scan.getAttribute( 'highMz' ))
			if ( scan.getAttribute( 'polarity' ) == '+' ):
				polarity = 1
			else:
				polarity = -1
			if msLevel == 1:
				parentScan = None
			else:
				parentScan = int( scan.parentNode.getAttribute( 'num' ))
				if ( scan.getAttribute( 'collisionEnergy' )):
					collisionEnergy = float( scan.getAttribute( 'collisionEnergy' ))
				precursorTags = scan.getElementsByTagName( 'precursorMz' )
				if ( len( precursorTags )):
					precursorMz = float( re.sub( r"<.*?>", "", precursorTags[ 0 ].toxml( )).strip( ))
			

			peaks = scan.firstChild
			while not ( peaks.nodeType == peaks.ELEMENT_NODE and peaks.tagName == 'peaks' ):
				peaks = peaks.nextSibling

			if peaks.getAttribute( 'precision' ) == '64':
				type = 'd'
			else: 
				type='f'
			byteOrder = '>'

			# get all of the text (non-tag) content of peaks
			packedData = re.sub( r"<.*?>", "", peaks.toxml( )).strip( )
			if ( peaks.getAttribute( 'compressionType' ) == 'zlib' ):
				data = struct.unpack( byteOrder + ( type * scanSize * 2 ), zlib.decompress( b64decode( packedData )))
			else:
				data = struct.unpack( byteOrder + ( type * scanSize * 2 ), b64decode( packedData ))
			massValues = data[ 0::2 ]
			intensityValues = data[ 1::2 ] 

			self.data[ "scans" ].append({ 
				"retentionTime" : rt,
				"polarity" : polarity, 
				"msLevel" : msLevel, 
				"id" : scanId,
				"lowMz" : lowMz,
				"highMz" : highMz,
				"parentScan" : parentScan,
				"precursorMz" : precursorMz,
				"collisionEnergy" : collisionEnergy,
				"points" : list( zip( massValues, intensityValues ))
			})
		return True


	def readMzMl( self, filename ):
		pass
		

	def _getChildNode( self, node, child ):
		"""
		Internal function. Finds the child node of the passed in xml node with the 
		given tag name.

		:Parameters:
			node : minidom node
				A minidom node object
			child : str
				A string containing the tag name of the child node to return.

		rtype: minidom node
		return: The requested child of the minidom node.
		"""
		returnvalue = node.firstChild
		while returnvalue and not ( 
			returnvalue.nodeType == returnvalue.ELEMENT_NODE and 
			returnvalue.tagName == child ):

			returnvalue = returnvalue.nextSibling
		return returnvalue

	def removeScans( self, minTime=0, maxTime=sys.maxint ):
		"""
		Discards all scans in the given time range.

		:Parameters:
			minTime : float
				The minimum retention time for the scans to remove
			maxTime : float
				The maximum retention time for the scans to remove
		"""
		if minTime < maxTime:
			self.data[ 'scans' ] = [ scan for scan in self.data['scans'] if 
			                           scan[ 'retentionTime' ] < minTime or 
			                           scan[ 'retentionTime' ] > maxTime ]

	def keepScans( self, minTime=0, maxTime=sys.maxint ):
		"""
		Keeps only the scans specified in the time range, discarding all others.

		:Parameters:
			minTime : float
				The minimum retention time for the scans to remove
			maxTime : float
				The maximum retention time for the scans to remove
		"""
		if minTime < maxTime:
			self.data[ 'scans' ] = [ scan for scan in self.data['scans'] if 
			                           scan[ 'retentionTime' ] > minTime and
			                           scan[ 'retentionTime' ] < maxTime ]

	def removeMz( self,  mz, tolerance=0.1 ):
		"""
		Discards all data points with the specified mass +/- the specified tolerance

		:Parameters:
			mz : float
				The m/z value of the mass to be removed from all scans.
			tolerance : float
				The tolerance to use for determining if the data point should be removed.
				Defaults to 0.1.
		"""
		for scan in self.data[ 'scans' ]:
			scan[ 'points' ] = [ point for point in scan[ 'points' ] if 
			                   point[ 0 ] < mz - tolerance or
			                   point[ 0 ] > mz + tolerance ]

	def onlyMz( self, mz, tolerance=0.1 ):
		"""
		Keeps only data points with the specified mass +/- the specified tolerance,
		discarding all others.

		:Parameters:
			mz : float
				The m/z value of the mass to be removed from all scans.
			tolerance : float
				The tolerance to use for determining if the data point should be removed.
				Defaults to 0.1.
		"""
		for scan in self.data[ 'scans' ]:
			scan[ 'points' ] = [ point for point in scan[ 'points' ] if 
												 point[ 0 ] > mz - tolerance and
												 point[ 0 ] < mz + tolerance ]


	def writeCsv( self, filename ):
		"""
		:Parameters:
			filename : string
				The name of the file to write to.

		rtype: bool
		return: True if the write succeeded
		"""
		out = open( filename, 'w' )
		out.write( "[data source]\n" )
		out.write( "file name,%s\n" % self.data[ 'sourceFile' ] )
		out.write( "[filters]\n" )
		out.write( "mass range,%f,%f\n" % 
						 ( min([ x[ 'lowMz' ] for x in self.data[ 'scans' ]]), 
						 ( max([ x[ 'highMz' ] for x in self.data[ 'scans' ]]))))
		rtList = [ x['retentionTime']  for x in self.data['scans']]
		out.write( "time range,%f,%f\n" % ( min( rtList ), max( rtList )))
		out.write( "number of spectra,%d\n" % len( self.data['scans'] ))
		out.write( "[format]\n" )
		out.write( "retention time, sample, period, experiment, polarity, scan type, points, x1, y1, x2, y2, ...\n" )
		out.write( "[spectra]\n" )
		level2 = False
		for scan in self.data[ 'scans' ]:
			if ( scan[ 'msLevel' ] > 1 ):
				if not level2:
					print( "Agilent CSV format does not support multimensional data, ignoring scans with level > 1" )
					level2 = True
				continue

			if ( scan[ 'polarity' ] > 0 ):
				polarity = '+'
			else:
				polarity = '-'
			out.write( "%f,%d,%d,%d,%s,%s,%d," % 
								( scan[ 'retentionTime' ], 1, 1, 1, polarity, "peak", 
								len( scan[ 'points' ])))
			for point in scan[ 'points' ]:
				out.write( '%f,%f,' % point )
			out.write( "\n" )
		out.close( )
			
	def writeMzData( self, filename ):
		pass

	def writeMzXML( self, filename ):
		pass

	def writeMzML( self, filename ):
		pass

	def writeJson( self, filename ):
		"""
		Dumps the data to a JSON array.
		:Parameters:
			maData : dict
				A dictionary object containing scan data, normally returned from
			filename : string
				The name of the file to write to.
		"""
		out = open( filename, 'w' )
		json.dump( self.data, out )
		out.close( )

	def writeJsonGz( self, filename, compressionLevel=6 ):
		"""
		Dumps the data to a JSON array, compressed with zlib.
		:Parameters:
			maData : dict
				A dictionary object containing scan data, normally returned from
			filename : string
				The name of the file to write to.
			compressionLevel : int
				Compression level to use - 0 for least compression, 9 for most.
				Defaults to 6.
		"""
		out = open( filename, 'w' )
		out.write( zlib.compress( json.dumps( self.data ), compressonLevel ))
		out.close( )


