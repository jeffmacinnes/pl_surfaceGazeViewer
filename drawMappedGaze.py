"""
Received streamed gaze coords. Gaze coords are normalized and mapped relative to the reference image. 
This script will overlay the gaze coords on top of the reference image

keyboard controls:
	- b: toggle background on/off
	- g: toggle gaze pts on/off
	- h: toggle heatmap on/off
	- r: reset all data pts
	- t: show ALL gaze pts, vs. trace (showGaze must be true, g-key)

	- [arrow keys]: manually adjust gaze pts location 

"""
from __future__ import print_function
from __future__ import division
import pygame
import pygame.gfxdraw
import sys
import zmq
import cv2
import argparse
import numpy as np 
import msgpack as serializer
from multiprocessing import Process, Array, Value
import time


def launchViewer(host, port, refImg):
	"""
	Main program
	Start listening for incoming data, show viewer in local window
	"""
	
	# flags for what to show
	showBG = True		# background image toggle
	showGaze = True		# gaze pts toggle
	showHM = False		# heatmap toggle
	allGaze = False		# show all gaze toggle (vs. gaze trace)
	gazeTrace = 100 	# number of pts in gaze trace

	# gaze settings
	xPts = Array('f', np.zeros(10000))
	yPts = Array('f', np.zeros(10000))
	nPts = Value('i', 0)
	xOffset = 0
	yOffset = 0
	
	dotColor = (254,91,161)
	lineColor = (0, 0, 0)

	# pygame setup
	pygame.init()
	bgImg = pygame.image.load(refImg)
	w = bgImg.get_width()
	h = bgImg.get_height()
	size = w,h

	pygame.display.list_modes()
	info = pygame.display.Info()
	screen = pygame.display.set_mode(size)	# window


	# start socket listening in the background
	p = Process(target=dataReceiver, args=(host, port, nPts, xPts, yPts))
	p.daemon = True
	p.start()

	# Viewer Loop
	running = True
	while running:
		### set up screen elements
		if showBG:
			# bg image
			screen.blit(bgImg, (0,0))
		else:
			screen.fill((0, 0, 0))

		# grab the indices for relevant datapoints
		if allGaze:
			startPt_idx = 0
		else:
			startPt_idx = nPts.value - gazeTrace   # set the range for how many pts you want to use
		if startPt_idx < 0: startPt_idx = 0
		lastPt_idx = nPts.value-1
		pt_indices = np.arange(startPt_idx, lastPt_idx+1)

		### create/show heatmap
		if showHM:
			if nPts.value > 5:
				# create numpy arrays from ctype Arrays xPts and yPts
				xArr = np.array(xPts[0:lastPt_idx])
				yArr = np.array(yPts[0:lastPt_idx])

				# create heatmap array
				try:
					hm_array, low_color = createHeatmap(size, xArr, yArr, xOffset, yOffset)
					keyColor = pygame.Color(low_color[0], low_color[1], low_color[2], int(255))

					# turn into a pygame surface and display
					hm_surf = pygame.surfarray.make_surface(hm_array[:,:,:3])
					hm_surf.set_colorkey(keyColor)
					hm_surf.set_alpha(205)
					screen.blit(hm_surf, (0,0))
				except:
					pass

		### show GazePts
		if showGaze:
		# make sure there's at least 2 points to draw (for the sake of a line)
			if len(pt_indices) >= 2:
				# loop through all pts
				for i, ptIdx in enumerate(pt_indices):
					
					### LINES
					# if it's the first point in the indices, can't draw a line yet
					if i == 0:
						prev_ptIdx = ptIdx
					else:
						# set up line coords
						x1 = int(xPts[prev_ptIdx] * size[0]) + xOffset
						y1 = int(yPts[prev_ptIdx] * size[1]) + yOffset
						x2 = int(xPts[ptIdx] * size[0]) + xOffset
						y2 = int(yPts[ptIdx] * size[1]) + yOffset

						if allGaze:
							thisLineColor = lineColor
						else:
							alpha = (i * 255/len(pt_indices))
							thisLineColor = lineColor + (alpha,)

						pygame.draw.aaline(screen, thisLineColor, (x1, y1), (x2, y2))

						# update the prevPt idx
						prev_ptIdx = ptIdx


					### CIRCLES
					cx = int(xPts[ptIdx] * size[0]) + xOffset
					cy = int(yPts[ptIdx] * size[1]) + yOffset
					if abs(cx) > 20000: cx = 20000
					if abs(cy) > 20000: cy = 20000
					
					if allGaze:
						# only draw current gaze pt circle, if showing all gaze pts
						if ptIdx == pt_indices.max():
							r = 36
							thisDotColor = (0, 99, 99)
							pygame.gfxdraw.filled_circle(screen, cx, cy, r, thisDotColor)
					
					else:
						# otherwise, draw circles and set transparency
						if allGaze:
							thisDotColor = dotColor
						else:
							alpha = (i * 255/len(pt_indices))
							thisDotColor = dotColor + (alpha,)
						
						if ptIdx == pt_indices.max():
							r = 24
							thisDotColor = (0, 99, 99)
						else:
							r = 12
						pygame.gfxdraw.filled_circle(screen, cx, cy, r, thisDotColor)


		# update the screen
		pygame.display.flip()

		# listen for commands/events
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
				pygame.quit()
				sys.exit()

			# keyboard commands
			if event.type == pygame.KEYDOWN:
				# toggle bg on/off with b key
				if event.key == pygame.K_b:
					if showBG:
						showBG = False
					else:
						showBG = True

				# toggle gaze pts on/off with g key
				elif event.key == pygame.K_g:
					if showGaze:
						showGaze = False
					else:
						showGaze = True

				# toggle gaze pts all vs. trace with t key
				elif event.key == pygame.K_t:
					if allGaze:
						allGaze = False
					else:
						allGaze = True

				# toggle hm on/off with h key
				elif event.key == pygame.K_h:
					if showHM:
						showHM = False
					else:
						showHM = True

				# reset all datapts
				elif event.key == pygame.K_r:
					nPts.value = 0

				# manual calibration with arrow keys
				elif event.key == pygame.K_UP:
					yOffset -= 5
				elif event.key == pygame.K_DOWN:
					yOffset += 5
				elif event.key == pygame.K_RIGHT:
					xOffset += 5
				elif event.key == pygame.K_LEFT:
					xOffset -= 5

				# quit
				if event.key == pygame.K_q:
					running = False
					pygame.quit()
					sys.exit()



def dataReceiver(host, port, nPts, xPts, yPts):
	"""
	receive data over socket, store in Arrays
	"""
	# set up socket
	context = zmq.Context()
	
	# send request to get the specific port number for this data
	requester = context.socket(zmq.REQ)
	requester.connect('tcp://%s:%s' %(host, port))
	requester.send_string('SUB_PORT')
	sub_port = requester.recv_string()
	print('received sub port:' + sub_port)

	# now open a new socket on this subport
	sub_socket = context.socket(zmq.SUB)
	sub_socket.connect('tcp://%s:%s' % (host, sub_port))

	# filter topics
	try:
		sub_socket.setsockopt(zmq.SUBSCRIBE, 'surface')
	except TypeError:
		sub_socket.setsockopt_string(zmq.SUBSCRIBE, 'surface')

	while True:
		topic, msg = sub_socket.recv_multipart()
		message = serializer.loads(msg)
		try:
			for gaze in message[b'gaze_on_srf']:
				#print(gaze[b'norm_pos'])
				thisX = gaze[b'norm_pos'][0]
				thisY = 1 - gaze[b'norm_pos'][1]
				if (thisX < 0) or (thisX > 1.5): thisX = 1.4
				if (thisY < 0) or (thisY > 1.5): thisY = 1.4
				xPts[nPts.value] = thisX
				yPts[nPts.value] = thisY		# invert (incoming coords have origin bottom left)
				nPts.value += 1
		except:
			pass



def createHeatmap(size, xArr, yArr, xOffset, yOffset):
	"""
	create a heatmap based on the supplied x & y pts
	return a numpy array that can be converted to a pygame surface and shown on the screen
	"""
	
	# calculate the number of bins in each direction
	w,h = size
	aspect_ratio = h/w
	bins_w = 25
	bins_h = int(bins_w * aspect_ratio)

	# convert the x/y data to be percentages of the bin ranges
	xArr = (xArr * bins_w)
	yArr = (yArr * bins_h)

	# add in any manual x/y offset. 
	# this offset is currenly a function of screen w/h, needs to be bins w/h
	xOffset_bins = (xOffset/w) * bins_w
	yOffset_bins = (yOffset/h) * bins_h
	xArr = xArr + xOffset_bins
	yArr = yArr + yOffset_bins

	# make 2d histogram
	hist, xedges, yedges = np.histogram2d(xArr, yArr, 
								bins=(bins_w, bins_h),
								range=[[0,bins_w], [0, bins_h]],
								normed=False)

	# smooth the histogram
	hm_detail = .5
	filter_size = int(int(hm_detail * bins_w)/2)*2 + 1
	std_dev = int(filter_size/6.)
	hist = cv2.GaussianBlur(hist, (filter_size, filter_size), std_dev)

	# normalize to 0-255
	maxval = np.amax(hist)
	scale = 255./maxval
	hist = np.uint8(hist*(scale))

	# threshold histogram
	hist[hist < 55] = 0

	# apply cv2 colormap to the histogram
	c_map = cv2.applyColorMap(hist, cv2.COLORMAP_COOL)

	# resize to match the full width and height of the image
	c_map = cv2.resize(c_map, (h,w))

	# convert the color to RGB from BGR
	c_map = cv2.cvtColor(c_map, cv2.COLOR_BGR2RGB)

	# create the np array that will store the heatmap
	heatmap = np.ones((w,h,4), dtype=np.uint8)
	heatmap[:,:,:3] = c_map
	heatmap[:,:, 3] = 120  # set transparency

	# get the color of the lowest values (in order to make transparent)
	zeroIdx = np.where(hist == 0)
	zeroColor = heatmap[zeroIdx[0][0], zeroIdx[1][0], :3].astype(int)

	return heatmap, zeroColor


if __name__ == '__main__':
	# parse arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('host', help='Host IP (eye data will be sent from this address)')
	parser.add_argument('port', help='Port Number (port number to connect over)')
	parser.add_argument('refImg', help='Path to reference image you want to overlay gaze onto')
	args = parser.parse_args()

	launchViewer(args.host, args.port, args.refImg) 




					





