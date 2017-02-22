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


def dataReceiver(nPts, xPts, yPts):
	"""
	receive data over socket, store in arr
	"""
	# set up socket
	host = '127.0.0.1'
	port = '42000'
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
		print('received:' + topic + ' message')

		thisGaze = payload['gaze']
		print(thisGaze[0])
		xPts[nPts.value] = thisGaze[0]
		yPts[nPts.value] = thisGaze[1]
		nPts.value += 1


### Screen settings
pygame.init()
size = 650, 650
screen = pygame.display.set_mode(size)
bgImg = pygame.image.load("startImage.jpg")

dotColor = (254,91,161)
lineColor = (170, 238, 180)
nTrace = 60

if __name__ == '__main__':
	# shared vars across processes
	xPts = Array('f', np.zeros(10000))
	yPts = Array('f', np.zeros(10000))
	nPts = Value('i', 0)
	
	# start socket listening process in the background
	p = Process(target=dataReceiver, args=(nPts, xPts, yPts))
	p.daemon = True
	p.start()

	while True:
		### set up screen elements
		# bg image
		screen.blit(bgImg, (0,0))

		if nPts.value > nTrace:
			# draw gaze lines
			for i in range(1, nTrace):
				prevIdx = i-1
				x1 = int(xPts[nPts.value-prevIdx - 1] * size[0])
				y1 = int(yPts[nPts.value-prevIdx - 1] * size[1])
				x2 = int(xPts[nPts.value-i -1] * size[0])
				y2 = int(yPts[nPts.value-i -1] * size[1])
				alpha = 255 - (i * (255/nTrace))
				thisLineColor = lineColor + (alpha,)

				pygame.gfxdraw.line(screen, x1, y1, x2, y2, thisLineColor)


			# draw gaze dots
			for i in range(1, nTrace):
				circleX = int(xPts[nPts.value - i - 1] * size[0])
				circleY = int(yPts[nPts.value - i - 1] * size[1])
				alpha = 255 - (i * (255/nTrace))
				thisDotColor = dotColor + (alpha,)
				pygame.gfxdraw.filled_circle(screen, circleX, circleY, 10, thisDotColor)

		pygame.display.flip()
		print(nPts.value)
