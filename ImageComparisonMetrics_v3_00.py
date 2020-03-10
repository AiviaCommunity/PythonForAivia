import os.path
import numpy as np
from skimage.io import imread, imsave
from skimage.util import img_as_uint, img_as_float32, img_as_ubyte
from skimage.metrics import mean_squared_error, structural_similarity
from skimage.exposure import match_histograms

"""
See: https://scikit-image.org/docs/dev/api/skimage.metrics.html?highlight=structural#skimage.metrics.structural_similarity

Outputs SSIM map as a result of the comparison of 2 channels. Second channel (Ground Truth Image) is adjusted by histogram matching.
First output channel is the GT adjusted image.

It is highly recommended to:
- Use LUT color mapping to better see the variations in the SSIM values

All real SSIM values (ranging from 0 to 1) can be retrieved from the map doing the following: divide intensities by 255 if image is 8-bit, or by 65535 if 16-bit.

Side note: MSE and mean SSIM (and NRMSE, PSNR) values are output in the log

To be able to see the printed info in the log file, set:
File > Options > Logging > Verbosity = everything

Other source:
https://scikit-image.org/docs/dev/auto_examples/color_exposure/plot_histogram_matching.html#sphx-glr-auto-examples-color-exposure-plot-histogram-matching-py

"""

# [INPUT Name:inputRTImagePath Type:string DisplayName:'Input Restored Image']
# [INPUT Name:inputGTImagePath Type:string DisplayName:'Input Ground Truth Image']
# [OUTPUT Name:resultPath Type:string DisplayName:'SSIM image']
# [OUTPUT Name:resultPathAdj Type:string DisplayName:'GT Hist match image']
def run(params):
	RTimageLocation = params['inputRTImagePath']
	GTimageLocation = params['inputGTImagePath']
	resultLocation = params['resultPath']
	resultLocationAdj = params['resultPathAdj']
	
	# Checking existence of temporary files (individual channels)
	if not os.path.exists(RTimageLocation):
		print(f'Error: {RTimageLocation} does not exist')
		return; 
	if not os.path.exists(GTimageLocation):
		print(f'Error: {GTimageLocation} does not exist')
		return; 
		
	# Loading input images
	RTData = imread(RTimageLocation)
	GTData = imread(GTimageLocation)
	print(f'Dimensions of Restored image: {RTData.shape}')
	print(f'Dimensions of GT image: {GTData.shape}')
	
	# Histogram matching
	matched_GTData = match_histograms(GTData, RTData).astype(RTData.dtype)
	
	# MSE measurement
	# valMSE = skimage.measure.compare_mse(RTData, GTData) # deprecated in scikit-image 0.18 
	valMSE = mean_squared_error(RTData, matched_GTData)
	print(f'___ MSE = {valMSE} ___')	# Value appears in the log if Verbosity option is set to 'Everything'
	
	# print(f'Restored: {RTData[0:10,0]}')	# DEBUG info
	# print(f'GT: {GTData[0:10,0]}')
	# print(f'Histogram matched GT: {matched_GTData[0:10,0]}')
	
	# SSIM measurement
	# outFullSSIM = skimage.measure.compare_ssim(RTData, GTData, full=True) # deprecated in scikit-image 0.18 
	# outFullSSIM = skimage.measure.compare_ssim(RTData, GTData, full=True, gaussian_weights=True, sigma=1.5, use_sample_covariance=False) # deprecated in scikit-image 0.18 
	outFullSSIM = structural_similarity(RTData, matched_GTData, full=True)
	
	# Extracting mean value (first item)
	outMeanSSIM = outFullSSIM[0]
	print(f'___ Mean SSIM = {outMeanSSIM} ___')
	
	# Extracting map (second item)
	outSSIM = outFullSSIM[1]
	print(f'Bit depth of SSIM array: {outSSIM.dtype}')

	
	# Convert output array whose range is [0-1] to adjusted bit range (8- or 16-bit)
	if RTData.dtype is np.dtype('u2'):
		outputData = img_as_uint(outSSIM)
	elif RTData.dtype is np.dtype('f4'):
		outputData = img_as_float32(outSSIM)	# necessary?
	else:
		outputData = img_as_ubyte(outSSIM)
	
	#print(outputData[0:10,0])	# DEBUG info

	
	imsave(resultLocation, outputData)	
	imsave(resultLocationAdj, matched_GTData)

# CHANGELOG
# v02 TL - Reorganized import functions to only import specific functions
#        - skimage.measure is still not found - do we not install this?
#
# v2.01 PM - Added conditional conversion of float64 output of SSIM calculation
#
# v3.00 PM - Added histogram matching function and output of GT adjusted image