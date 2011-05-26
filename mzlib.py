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


	Version alpha 2011.05.26

"""
import sys
import os
from xml.dom.minidom import parse
import struct
from base64 import b64decode
import re
import zlib
import gzip
from copy import deepcopy
try: 
	import json
except ImportError:
	try:
		import simplejson as json
	except:
		json = False

class RawData( object ):

	def __init__( self, _input=None ):
		if type( _input ) == RawData:
			# copy the passed in object
			self.data = deepcopy( _input.data )

		elif type( _input ) == str:
			# read the passed in file name
			self.read( _input )

		else:
			self.data = { 'scans' : [] }

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
			currentDifference = abs( scan[ 'retentionTime' ] - retentionTime )
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
			if ( value.start ):
				start = value.start 
			else:
				start = 0
			if ( value.stop ):
				stop = value.stop 
			else:
				stop = 1048576
			return self.sic( start, stop, 1 )
		else:
			return self.sic( value - 0.1, value + 0.1, 1 )

	def __iter__( self ):
		return iter( self.data['scans'] )

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
						scan[ 'retentionTime' ] >= maxTime ]

	def onlyScans( self, minTime=0, maxTime=sys.maxint ):
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
					scan[ 'retentionTime' ] >= minTime and
					scan[ 'retentionTime' ] < maxTime ]

	def removeMz( self,  mz, tolerance=0.1 ):
		"""
		Discards all data points with the specified m/z +/- the specified tolerance

		:Parameters:
			mz : float
				The m/z value of the mass to be removed from all scans.
			tolerance : float
				The tolerance to use for determining if the data point should be removed.
				Defaults to 0.1.
		"""
		for scan in self.data[ 'scans' ]:
			try:
				scan[ 'mzArray' ], scan[ 'intensityArray' ] = list( zip( 
							*[ point for point in zip( scan[ 'mzArray' ], scan[ 'intensityArray' ]) 
							if point[ 0 ] < mz - tolerance or
							point[ 0 ] >= mz + tolerance ]))
			except ValueError:
				scan[ 'mzArray' ] = []
				scan[ 'intensityArray' ] = []

	def onlyMz( self, mz, tolerance=0.1 ):
		"""
		Keeps only data points with the specified m/z +/- the specified tolerance,
		discarding all others.

		:Parameters:
			mz : float
				The m/z value of the mass to be retained from all scans.
			tolerance : float
				The tolerance to use for determining if the data point should be removed.
				Defaults to 0.1.
		"""
		for scan in self.data[ 'scans' ]:
			try:
				scan[ 'mzArray' ], scan[ 'intensityArray' ] = list( zip( 
							*[ point for point in zip( scan[ 'mzArray' ], scan[ 'intensityArray' ]) 
							if point[ 0 ] >= mz - tolerance and
							point[ 0 ] < mz + tolerance ]))
			except ValueError:
				scan[ 'mzArray' ] = []
				scan[ 'intensityArray' ] = []

	def sic( self, start=0, stop=1048576, level=1 ):
		"""
		Returns a list indicating the selected intensity for each scan in order. 
		:Parameters:
			start : float
				The m/z indices to retrieve intensity values higher than or equal to.
			stop : float
				The m/z indecies to retrieve intensity values less than.
			level : int
				The msLevel of the scans to get intensity values for. A value of 0 
				uses all scans.

		rtype: list
		return: A list of intensity values.
		"""
		returnvalue = []
		for scan in self.data[ 'scans' ]:
			if not level or ( scan[ 'msLevel' ] == level ):
				returnvalue.append( sum([ int_ for mz,int_ in 
				      zip( scan[ 'mzArray' ], scan[ 'intensityArray' ])
							if mz >= start and mz < stop ]))
		return returnvalue

	def tic( self, level=1 ):
		"""
		Returns a list indicating the total intensity for each scan in order. 
		:Parameters:
			level : int
				The msLevel of the scans to get intensity values for. A value of 0 
				uses all scans.

		rtype: list
		return: A list of intensity values.
		"""
		return [ sum( scan[ 'intensityArray' ]) for scan in self.data[ 'scans' ]
		         if ( not level or ( scan[ 'msLevel' ] == level ))]

	def bpc( self, level=1 ):
		"""
		Returns a list indicating the base intensity for each scan in order. 
		:Parameters:
			level : int
				The msLevel of the scans to get intensity values for. A value of 0
				uses all scans

		rtype: list
		return: A list of intensity values.
		"""
		return [ max( scan[ 'intensityArray' ]) for scan in self.data[ 'scans' ] 
		         if ( not level or ( scan[ 'msLevel' ] == level ))]


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

		if filename.lower( ).endswith( ".csv" ):
			return self.readCsv( filename )

		elif filename.lower( ).endswith( ".mzdata" ) or filename.endswith(  ".mzdata.xml" ):
			return self.readMzData( filename )

		elif filename.lower( ).endswith( ".mzxml" ):
			return self.readMzXml( filename )

		elif filename.lower( ).endswith( ".mzml" ):
			return self.readMzMl( filename )

		elif filename.lower( ).endswith( ".json" ):
			return self.readJson( filename )

		elif filename.lower( ).endswith( ".json.gz" ):
			return self.readJsonGz( filename )

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
				"mzRange" : [ min( massValues ), max( massValues ) ],
				"parentScan" : None,
				"precursorMz" : None,
				"collisionEnergy" : None,
				"mzArray" : massValues,
				"intensityArray" : intensityValues
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
				"mzRange" : [ lowMz, highMz ],
				"parentScan" : parentScan,
				"precursorMz" : precursorMz,
				"collisionEnergy" : collisionEnergy,
				"mzArray" : list( massValues ),
				"intensityArray" : list( intensityValues )
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
				"mzRange" : [ lowMz, highMz ],
				"parentScan" : parentScan,
				"precursorMz" : precursorMz,
				"collisionEnergy" : collisionEnergy,
				"mzArray" : list( massValues ),
				"intensityArray" : list( intensityValues )
			})
		return True


	def readMzMl( self, filename ):
		raise NotImplementedError( 
			"Reading from this file type has not yet been implemented." )
		

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

	def readJson( self, filename ):
		"""
		Reads ms data from a file containing gzipped JSON data. No checks are done, 
		so make sure the data is of the same format as that produced by this 
		library, otherwise, unpredictable things may happen. This method may not be
		supported on versions of python prior to 2.5.
		:Parameters:
			filename : string
				The name of a file containing gzip compressed JSON data
		"""
		if not json:
			raise NotImplementedError( "This method is not supported in your version of Python" )
		in_ = open( filename )
		self.data = json.load( in_ )
		in_.close( )
		return True

	def readJsonGz( self, filename ):
		"""
		Reads ms data from a file containing gzipped JSON data. No checks are done, 
		so make sure the data is of the same format as that produced by this 
		library, otherwise, unpredictable things may happen. This method may not be
		supported on versions of python prior to 2.5.
		:Parameters:
			filename : string
				The name of a file containing gzip compressed JSON data
		"""
		if not json:
			raise NotImplementedError( "This method is not supported in your version of Python" )
		in_ = gzip.open( filename )
		self.data = json.load( in_ )
		in_.close( )
		return True

	def write( self, filename ):
		"""
		Load a file into this reference. This method will automatically detect the
		file type based on the file extension.

		:Parameters:
			filename : str
				The name of the file to load.

		"""
	
		if filename.lower( ).endswith( ".csv" ):
			return self.writeCsv( filename )

		elif ( filename.lower( ).endswith( ".mzdata" ) or 
		       filename.lower( ).endswith(  ".mzdata.xml" )):
			return self.writeMzData( filename )

		elif filename.lower( ).endswith( ".mzxml" ):
			return self.writeMzXml( filename )

		elif filename.lower( ).endswith( ".mzml" ):
			return self.writeMzMl( filename )

		elif filename.lower( ).endswith( ".json" ):
			return self.writeJson( filename )

		elif filename.lower( ).endswith( ".json.gz" ):
			return self.writeJsonGz( filename )

		else:
			sys.stderr.write( "Unrecognized file type for %s\n" % filename )
			return False

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
						 ( min([ x[ 'mzRange' ][ 0 ] for x in self.data[ 'scans' ]]), 
						 ( max([ x[ 'mzRange' ][ 1 ] for x in self.data[ 'scans' ]]))))
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
								len( scan[ 'mzArray' ])))
			for point in zip( scan[ 'mzArray' ], scan[ 'intensityArray' ]):
				out.write( '%f,%f,' % point )
			out.write( "\n" )
		out.close( )
			
	def writeMzData( self, filename ):
		raise NotImplementedError( 
			"Writing to this file type has not yet been implemented." )

	def writeMzXML( self, filename ):
		raise NotImplementedError( 
			"Writing to this file type has not yet been implemented." )

	def writeMzML( self, filename ):
		raise NotImplementedError( 
			"Writing to this file type has not yet been implemented." )

	def writeJson( self, filename, indent=None ):
		"""
		Dumps the data to a JSON array.
		:Parameters:
			maData : dict
				A dictionary object containing scan data, normally returned from
			filename : string
				The name of the file to write to.
			indent : int
				Level to indent for pretty-printing, or None for no pretty-print.
				Defaults to None
		"""
		if not json:
			raise NotImplementedError( "This method is not supported in your version of Python" )
		if( indent ):
			sep = (', ',': ')
		else:
			sep = (',',':')
		out = open( filename, 'w' )
		json.dump( self.data, out, indent=indent, separators=sep )
		out.close( )

	def writeJsonGz( self, filename, indent=None, compressionLevel=6 ):
		"""
		Dumps the data to a JSON array, compressed with zlib.
		:Parameters:
			maData : dict
				A dictionary object containing scan data, normally returned from
			filename : string
				The name of the file to write to.
			indent : int
				Level to indent for pretty-printing, or None for no pretty-print.
				Defaults to None
			compressionLevel : int
				Compression level to use - 0 for least compression, 9 for most.
				Defaults to 6.
		"""
		if( indent ):
			sep = (', ',': ')
		else:
			sep = (',',':')
		out = gzip.open( filename, 'wb', compressionLevel )
		out.write( json.dumps( self.data, indent=indent, separators=sep))
		out.close( )


