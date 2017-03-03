"""
Received streamed gaze coords. Gaze coords are normalized and mapped relative to the reference image. 
This script will overlay the gaze coords on top of the reference image
"""
from __future__ import print_function
from __future__ import division
import pygame
import pygame.gfxdraw
import sys
import zmq
import cv2
import numpy as np 
import msgpack as serializer
from multiprocessing import Process, Array, Value
import time


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
				xPts[nPts.value] = gaze[b'norm_pos'][0]
				yPts[nPts.value] = 1 - gaze[b'norm_pos'][1]		# invert (incoming coords have origin bottom left)
				nPts.value += 1
		except:
			pass



def createHeatmap(xArr, yArr, xOffset, yOffset):
	"""
	create a heatmap based on the supplied x & y pts
	return a numpy array that can be converted to a surface and shown on the screen
	"""
	
	# calculate the number of bins in each direction
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

	# apply cv2 colormap to the histogram
	c_map = cv2.applyColorMap(hist, cv2.COLORMAP_SUMMER)

	# resize to match the full width and height of the image
	c_map = cv2.resize(c_map, (h,w))

	# create the np array that will store the heatmap
	heatmap = np.ones((w,h,4), dtype=np.uint8)
	heatmap[:,:,:3] = c_map
	heatmap[:,:, 3] = 120  # set transparency

	return heatmap


# Network Settings
host = '127.0.0.1'
#host = '10.188.90.175'
port = '50020'

#### pygame setup #######################
pygame.init()
bgImg = pygame.image.load("refImgs/histBook.jpg")
w = bgImg.get_width()
h = bgImg.get_height()
size = w,h

pygame.display.list_modes()
info = pygame.display.Info()
screen = pygame.display.set_mode(size)	# window
#screen = pygame.display.set_mode(size, pygame.FULLSCREEN) 	# full screen

dotColor = (254,91,161)
lineColor = (170, 238, 180)
showBG = True		# background image toggle
showHM = True		# heatmap toggle

### gaze settings
xOffset = 0
yOffset = 0

if __name__ == '__main__':

	# shared vars across processes
	xPts = Array('f', np.zeros(10000))
	yPts = Array('f', np.zeros(10000))
	nPts = Value('i', 0)

	# start socket listening in the background
	p = Process(target=dataReceiver, args=(host, port, nPts, xPts, yPts))
	p.daemon = True
	p.start()


	running = True
	while running:
		### set up screen elements
		if showBG:
			# bg image
			screen.blit(bgImg, (0,0))
		else:
			screen.fill((0, 0, 0))

		# grab the indices for relevant datapoints
		startPt_idx = nPts.value - 300   # set the range for how many pts you want to use
		if startPt_idx < 0: startPt_idx = 0
		lastPt_idx = nPts.value-1
		pt_indices = np.arange(startPt_idx, lastPt_idx+1)

		# create heatmap, if necessary
		if showHM:
			if nPts.value > 5:
				# create numpy arrays from ctype Arrays xPts and yPts
				xArr = np.array(xPts[0:lastPt_idx])
				yArr = np.array(yPts[0:lastPt_idx])

				hm_array = createHeatmap(xArr, yArr, xOffset, yOffset)

				#print(hm_array.shape)

				# turn into a pygame surface and display
				#hm_surf = pygame.surfarray.make_surface(hm_array[:,:,:3])
				hm_surf = pygame.Surface((w,h), pygame.SRCALPHA)
				#pygame.pixelcopy.array_to_surface(hm_surf, hm_array)
				hm_surf.set_alpha(175)
				screen.blit(hm_surf, (0,0))


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

					alpha = (i * 255/len(pt_indices))
					thisLineColor = lineColor + (alpha,)

					pygame.gfxdraw.line(screen, x1, y1, x2, y2, thisLineColor)

					# update the prevPt idx
					prev_ptIdx = ptIdx


				### CIRCLES
				cx = int(xPts[ptIdx] * size[0]) + xOffset
				cy = int(yPts[ptIdx] * size[1]) + yOffset
				alpha = (i * 255/len(pt_indices))
				thisDotColor = dotColor + (alpha,)
				if ptIdx == pt_indices.max():
					r = 12
				else:
					r = 6
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

				# toggle hm on/off
				if event.key == pygame.K_h:
					if showHM:
						showHM = False
					else:
						showHM = True

				# manual calibration with arrow keys
				if event.key == pygame.K_UP:
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
					sys.exist()





