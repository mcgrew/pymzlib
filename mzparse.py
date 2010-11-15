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


	Version 0.1-beta-2010.07.23
"""
import sys
import os
#import tempfile
#from hashlib import sha1
#import cPickle
import numpy as numerical
import libxml2 as xml
import struct
from base64 import b64decode
import types
try:
	import filters
except ImportError,e:
	filters = None

class MzData( object ):

	rt = None
	count = None
	mass = None
	intensity = None
	polarity = None
	sourceFile = None


	def __init__( self, options=None ):
		"""
		Initializes a MzData object.

		:Parameters:
			options : None
				This argument is deprecated and not used. Only here for compatibility.
		"""
		object.__init__( self )

	def read( self, filename ):
		"""
		Load a file into this reference. This method will automatically detect the
		file type based on the file extrension.

		:Parameters:
			filename : str
				The name of the file to load.
		"""

		if not os.path.exists( filename ):
			raise IOError( "The file %s does not exist or is not readable" % filename )

		# look for a cached version of this file
#		tmpDir = tempfile.gettempdir( ) + os.path.sep + "plotXmass"
#		cacheFileName = tmpDir + os.path.sep + sha1( "%s %d" % ( filename, os.path.getsize( filename ))).hexdigest( )
#		if not os.path.exists( tmpDir ):
#			os.mkdir( tmpDir )
#		else:
#			if os.path.exists( cacheFileName ):
#				cacheFile = open( cacheFileName, 'rb' )
#				try:
#					self.rt = cPickle.load( cacheFile ) 
#					self.mass = cPickle.load( cacheFile ) 
#					self.intensity = cPickle.load( cacheFile )
#					cacheFile.close( )
#				except ( cPickle.UnpicklingError ):
#					# bad file
#					cacheFile.close( )
#					os.remove( cacheFileName )


		try:
			fileExt = filename[ filename.rindex( '.' )+1: ]
		except ValueError:
			return False

		if ( fileExt.lower( ) == "csv" ):
			returnvalue =  self.readCsv( filename )

		elif ( fileExt.lower( ) == "mzdata" ):
			returnvalue = self.readMzData( filename )

		elif ( fileExt.lower( ) == "mzxml" ):
			returnvalue =  self.readMzXml( filename )
		else:
			sys.stderr.write( "Unrecognized file type for %s\n" % filename )
			return False

		if not returnvalue:
			return False
		return True

		#cache this file
#		if not ( os.path.exists( cacheFileName )):
#			cacheFile = open( cacheFileName, 'wb' )
#			try:
#				cPickle.dump( self.rt, cacheFile, cPickle.HIGHEST_PROTOCOL )
#				cPickle.dump( self.mass, cacheFile, cPickle.HIGHEST_PROTOCOL )
#				cPickle.dump( self.intensity, cacheFile, cPickle.HIGHEST_PROTOCOL )
#				cacheFile.close( )
#			except IOError,e:
#				sys.stderr.write( "Unable to cache file '%s'\n" % filename )
#				print e
#				cacheFile.close( )
#				os.remove( cacheFileName )

	def readCsv( self, filename ):
		"""
		Read a file in Agilent csv format. You should only use this method if you
		know the data is in this format and does not have the .csv extension.

		:Parameters:
			filename : str
				The name of the file to load.
		"""
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
		this.sourceFile = lines[ i ].split( ',' )[ 1 ]
		while ( i < len( lines ) and lines[ i ][ :9 ] != "[spectra]" ):
			i+=1
		i+=1
	
		if ( i > len( lines ) ):
			sys.stderr.write( "Unable to parse the reference file '%s'\n" % filename ) 
			return False
	
		rt = [] # retention time
		count = [] 
		mass = []
		intensity = []
		polarity = []
		# form the data into arrays.
		for line in lines[ i: ]:
			values = line.split( ',' )
			if values[ 4 ] == '-':
				polarity[ i ] = -1
			else:
				polarity[ i ] = 1
			rtValue = float( values[ 0 ])
			countValue = float( values[ 6 ])
			intensityValues = [  int( x )  for x in values[ 8:-1:2 ] ]
			massValues = [ float( y ) for y in values[ 7:-1:2 ] ]
			rt.append( rtValue )
			count.append( countValue )
			mass.append( massValues )
			intensity.append( intensityValues )
		# make the length of each row the same in the 2-d arrays (fill with zeros)
		maxLen = max([ len(x) for x in intensity ])
		for i in xrange( len( intensity )):
			mass[i].extend( [0] * ( maxLen - len( mass[ i ] )))
			intensity[i].extend( [0] * ( maxLen - len( intensity[ i ] )))

		#convert the arrays to numpy arrays
		self.rt = numerical.array( rt )
		self.polarity = numerical.array( polarity )
		self.count = numerical.array( count )
		self.mass = numerical.array( mass )
		self.intensity = numerical.array( intensity )

		return True
	readFile = read #readFile is an alias for read

	def readMzData( self, filename ):
		"""
		Read a file in mzData format. You should only use this method if you
		know the data is in this format and does not have the .mzdata extension.

		:Parameters:
			filename : str
				The name of the file to load.
		"""
		dataFile = xml.parseFile( filename )
		self.sourceFile = dataFile.xpathEval( '//sourceFile/nameOfFile' )[ 0 ].content
		scans = dataFile.xpathEval( '//spectrum' )
		scanSize = max(( int( i.content ) for i in dataFile.xpathEval( '//data/@length' )))
		self.rt = numerical.ndarray(( len( scans ), ))
		self.polarity = numerical.ndarray(( len( scans ), ))
		self.count = numerical.ndarray(( len( scans ), ), numerical.int32 )
		self.mass = numerical.zeros(( len( scans ), scanSize ))
		self.intensity = numerical.zeros(( len( scans ), scanSize ))
		for i in xrange( len( scans )):
			scan = scans[ i ]
			polarity = scan.xpathEval( '*//cvParam[@name="Polarity"]/@value' )
			if ( polarity == "Negative" ):
				self.polarity[ i ] = -1
			else:
				self.polarity[ i ] = 1
			self.rt[ i ] = float( scan.xpathEval( 
				'*//cvParam[@name="TimeInMinutes"]/@value' )[0].content )
			data = self._unpackMzData( scan.xpathEval( 'mzArrayBinary/data' )[ 0 ] )
			self.mass[ i ][ 0:len( data ) ] = data 
			data = self._unpackMzData( scan.xpathEval( 'intenArrayBinary/data' )[ 0 ] )
			self.intensity[ i ][ 0:len( data ) ] = data
			self.count[ i ] = len( data )

		return True

	def _unpackMzData( self, dataNode ):
		"""
		Internal function. Unpacks the scan data contained in a <data> node in mzdata 
		format.
	
		:Parameters:
			dataNode : xmlNode
				The xml node containing the scan data to be unpacked.
		"""
		prop = dataNode.properties
		while prop:
			if prop.name == 'length':
				scanSize = int( prop.content )
			if prop.name == 'endian':
				endian = prop.content 
			if prop.name == 'precision':
				precision = int( prop.content )
			prop = prop.next

#		if precision == 64: type = 'd'
#		else: type='f'
#		if littleEndian: byteOrder = '<'
#		else: byteOrder = '>'

#		return struct.unpack( byteOrder + ( type * scanSize ), b64decode( dataNode.content ))

		if precision == 64: type = numerical.float64
		else: type = numerical.float32
		if not endian == sys.byteorder:
			if endian == 'little': type = numerical.dtype( type ).newbyteorder( '<' )
			else: type = numerical.dtype( type ).newbyteorder( '>' )

		return numerical.frombuffer( b64decode( dataNode.content ), type, scanSize )

	def readMzXml( self, filename ):
		"""
		Read a file in mzXML format. You should only use this method if you
		know the data is in this format and does not have the .mzxml extension.

		:Parameters:
			filename : str
				The name of the file to load.
		"""
		dataFile = xml.parseFile( filename )
		dataContext = dataFile.xpathNewContext( )
		dataContext.xpathRegisterNs( 'def', dataFile.getRootElement( ).ns( ).getContent( ))
		scans = dataContext.xpathEval( '//def:scan[@msLevel="1"]' )
		scanSize = max(( int( i.content) for i in dataContext.xpathEval( '//def:scan[@msLevel="1"]/@peaksCount' )))
		self.rt = numerical.zeros(( len( scans), ))
		self.count = numerical.ndarray(( len( scans ), ), numerical.int32 )
		self.mass = numerical.zeros(( len( scans ), scanSize ))
		self.intensity = numerical.zeros(( len( scans ), scanSize ))
		for i in xrange( len( scans )):
			scan = scans[ i ]
			prop = scan.properties
			while prop:
				if prop.name == 'peaksCount':
					self.count[ i ] = int( prop.content )
				if prop.name == 'retentionTime':
					self.rt[ i ] = float( prop.content[ 2:-1 ] ) / 60
				prop = prop.next

			peaks = scan.children
			while peaks and not peaks.name == 'peaks': 
				peaks = peaks.next
			if not peaks:
				continue
			precision = peaks.properties
			while not precision.name == 'precision':
				precision = precision.next
			precision = int( precision.content )

#			if precision == 64: type = 'd'
#			else: type='f'
#			byteOrder = '>'

			if precision == 64: type = numerical.float64 
			else: type = numerical.float32
			if sys.byteorder == 'little':
				type = numerical.dtype( type ).newbyteorder( '>' )

			data = numerical.frombuffer( b64decode( peaks.content ), type, self.count[ i ] * 2 )
#			data = struct.unpack( byteOrder + ( type * scanSize * 2 ), b64decode( peaks.content ))
			self.mass[ i ][ 0:len( data )>>1 ] = data[ 0::2 ]
			self.intensity[ i ][ 0:len( data )>>1 ] = data[ 1::2 ] 

		return True

	def filterByTime( self, minTime=0, maxTime=0 ):
		"""
		Filters the data by retention time, removing any unwanted data

		:Parameters:
			minTime : float
				The minimum retention time to keep in this Object.
			maxTime : float
				The maximum retention time to keep in this Object.
		"""
		if ( minTime or maxTime ):
			minIndex, maxIndex = ( 0, len( self.rt ) + 1 )			
			for i in xrange( len( self.rt )): 
				if ( self.rt[ i ] < minTime ):
					minIndex = i
				if ( maxTime and self.rt[ i ] > maxTime ):
					maxIndex = i
					break
			minIndex += 1
			self.rt = self.rt[ minIndex:maxIndex ]
			self.mass =  self.mass[ minIndex:maxIndex ]
			self.intensity = self.intensity[ minIndex:maxIndex ]
			self.firstIndex = i

	def filterByMass( minMass=0, maxMass=0 ):
		"""
		Filters the data to keep only a certain mass range
		The data size is not changed, data which is not retained is zeroed.

		:Parameters:
			minMass : float
				The minimum mass to retain.
			maxMass : float
				The maximum mass to retain.
		"""
		for i in xrange( len( self.rt )): 
			for j in xrange( len( self.mass[ i ])):
				if ( self.mass[ i ][ j ] < minMass or self.mass[ i ][ j ] > maxMass ):
					self.mass[ i ][ j ] = 0
					self.intensity[ i ][ j ] = 0

		return True 

