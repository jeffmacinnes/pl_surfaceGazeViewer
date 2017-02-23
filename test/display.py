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
	receive data over socket, store in arr
	"""
	# set up socket
	# host = '127.0.0.1'
	# port = '42000'
	context = zmq.Context()
	sub_socket = context.socket(zmq.SUB)
	sub_socket.connect('tcp://%s:%s' % (host, port))

	# filter topics
	try:
		sub_socket.setsockopt(zmq.SUBSCRIBE, 'test')
	except TypeError:
		sub_socket.setsockopt_string(zmq.SUBSCRIBE, 'test')

	while True:
		topic = sub_socket.recv_string()
		payload = serializer.loads(sub_socket.recv(), encoding='utf-8')
		#print('received:' + topic + ' message')

		thisGaze = payload['gaze']
		xPts[nPts.value] = thisGaze[0]
		yPts[nPts.value] = thisGaze[1]
		nPts.value += 1


# Network Settings
host = '127.0.0.1'
host = '10.188.90.175'
port = '42000'

### Screen settings
pygame.init()
size = 650, 650
screen = pygame.display.set_mode(size)
bgImg = pygame.image.load("startImage.jpg")

dotColor = (254,91,161)
lineColor = (170, 238, 180)
showBG = True

if __name__ == '__main__':
	# shared vars across processes
	xPts = Array('f', np.zeros(10000))
	yPts = Array('f', np.zeros(10000))
	nPts = Value('i', 0)
	
	# start socket listening process in the background
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
		startPt_idx = nPts.value - 60
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

		pygame.display.flip()
		print(nPts.value)

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

