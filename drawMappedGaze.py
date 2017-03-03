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
				print(gaze[b'norm_pos'])
				xPts[nPts.value] = gaze[b'norm_pos'][0]
				yPts[nPts.value] = 1 - gaze[b'norm_pos'][1]		# invert (incoming coords have origin bottom left)
				nPts.value += 1
		except:
			pass


# Network Settings
host = '127.0.0.1'
#host = '10.188.90.175'
port = '50020'

# pygame setup
pygame.init()
bgImg = pygame.image.load("refImgs/histBook.jpg")
w = bgImg.get_width()
h = bgImg.get_height()
size = w,h
screen = pygame.display.set_mode(size)

dotColor = (254,91,161)
lineColor = (170, 238, 180)
showBG = True

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
		startPt_idx = nPts.value - 300
		lastPt_idx = nPts.value-1
		pt_indices = np.arange(startPt_idx, lastPt_idx+1)
		pt_indices = pt_indices[pt_indices >= 0] 		# remove negative indices (possible in beginning if startPt_idx is nPts-[something] )

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
					x1 = int(xPts[prev_ptIdx] * size[0])
					y1 = int(yPts[prev_ptIdx] * size[1])
					x2 = int(xPts[ptIdx] * size[0])
					y2 = int(yPts[ptIdx] * size[1])

					alpha = (i * 255/len(pt_indices))
					thisLineColor = lineColor + (alpha,)

					pygame.gfxdraw.line(screen, x1, y1, x2, y2, thisLineColor)

					# update the prevPt idx
					prev_ptIdx = ptIdx


				### CIRCLES
				cx = int(xPts[ptIdx] * size[0])
				cy = int(yPts[ptIdx] * size[1])
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
				if event.key == pygame.K_s:
					if showBG:
						showBG = False
					else:
						showBG = True