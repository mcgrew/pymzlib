"""
Filter.py

Author: Thomas McGrew

License:
	MIT license.
 
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
"""

import numpy as numerical

def lpf2d( data, threshold ):
	"""
	Performs a low pass filter on the passed in data.
	:Parameters:
		data : numerical.ndarray
			A 2 dimensional array (matrix) to be filtered
		threshold : int
			The position of the cutoff for the filter. Should be from 0 to 1

	rtype: numerical.ndarray
	returns: The filtered data
	"""
	fftData = numerical.fft.fft2( data )
	width, height = fftData.shape
	for x in xrange( width ):
		for y in xrange( height ):
			if not _insideCircle( x, y, width, height, threshold ):
				fftData[x][y] = 0
	return abs( numerical.fft.ifft2( fftData ))

def hpf2d( data, threshold ):
	"""
	Performs a high pass filter on the passed in data.
	:Parameters:
		data : numerical.ndarray
			A 2 dimensional array (matrix) to be filtered
		threshold : int
			The position of the cutoff for the filter. Should be from 0 to 1

	rtype: numerical.ndarray
	returns: The filtered data
	"""
	fftData = numerical.fft.fft2( data )
	width, height = fftData.shape
	for x in xrange( width ):
		for y in xrange( height ):
			if _insideCircle( x, y, width, height, threshold ):
				fftData[x][y] = 0
	return abs( numerical.fft.ifft2( fftData ))

def lpf( data, threshold ):
	"""
	Performs a low pass filter on the passed in data.
	:Parameters:
		data : numerical.ndarray
			A 1 dimensional array to be filtered
		threshold : int
			The position of the cutoff for the filter. Should be from 0 to 1

	rtype: numerical.ndarray
	returns: The filtered data
	"""
	data = numerical.array( data )
	fftData = numerical.fft.fft( data )
	x = data.shape[0]
	length = int(( x * threshold ) / 2 )
	if not length:
		return data
	fftData[ length:-length ] = [0] * ( x - ( length * 2 ))
	return numerical.fft.ifft( fftData )

def hpf( data, threshold ):
	"""
	Performs a high pass filter on the passed in data.
	:Parameters:
		data : numerical.ndarray
			A 1 dimensional array to be filtered
		threshold : int
			The position of the cutoff for the filter. Should be from 0 to 1

	rtype: numerical.ndarray
	returns: The filtered data
	"""
	data = numerical.array( data )
	fftData = numerical.fft.fft( data )
	x = data.shape[0]
	length = int(( x * threshold ) / 2 )
	if not length:
		return data
	fftData[  :length ] = [0] * length
	fftData[ -length: ] = [0] * length
	return numerical.fft.ifft( fftData )

def bpf( data, lowThreshold, highThreshold ):
	"""
	Performs a band pass filter on the passed in data.
	:Parameters:
		data : numerical.ndarray
			A 1 dimensional array to be filtered
		lowThreshold : int
			The position of the cutoff for the high pass filter. Should be from 0 to 1
		highThreshold : int
			The position of the cutoff for the low pass filter. Should be from 0 to 1

	rtype: numerical.ndarray
	returns: The filtered data
	"""
	data = numerical.array( data )
	fftData = numerical.fft.fft( data )
	x = data.shape[0]
	length = int(( x * highThreshold ) / 2 )
	if length:
		fftData[ length:-length ] = [0] * ( x - ( length * 2 ))
	length = int(( x * lowThreshold ) / 2 )
	if length:
		fftData[  :length ] = [0] * length
		fftData[ -length: ] = [0] * length
	return numerical.fft.ifft( fftData )

def _insideCircle( x, y, width, height, threshold ):
	"""
	Determines whether a particular position in the matrix is above or below the threshold

	rtype: bool
	returns: true if it is below the threshold, false otherwise
	"""
	fullDistance = math.sqrt( 2 * ( width/ 2 )**2 )
	#distance = math.sqrt( abs( width/2 - x )**2 + ( float( abs( height/2 - y )) * width /  height) ** 2 )
	distance = math.sqrt( min( x, width - x )**2 + ( float( min( y, height - y )) * width /  height) ** 2 )
	return ( threshold > distance / fullDistance )

