from __future__ import print_function
import pygame
import pygame.gfxdraw
import sys
import zmq
import numpy as np 
from multiprocessing import Process, Array, Value
import time


def dataReceiver(nPts, gazePts):
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
		msg = sub_socket.recv_string()
		print('received %s' % msg)
		gazePts[nPts.value] = float(msg.split(' ')[1])
		nPts.value += 1


### Screen settings
pygame.init()
size = 650, 650
screen = pygame.display.set_mode(size)
bgImg = pygame.image.load("startImage.jpg")


if __name__ == '__main__':
	# shared vars across processes
	gazePts = Array('f', np.zeros(1000))
	nPts = Value('i', 0)
	
	# start socket listening process in the background
	p = Process(target=dataReceiver, args=(nPts, gazePts))
	p.daemon = True
	p.start()

	while True:
		### set up screen elements
		# bg image
		screen.blit(bgImg, (0,0))

		# draw gaze locations
		for i in range(nPts.value):
			thisCircle = gazePts[i]
			pygame.gfxdraw.filled_circle(screen, int(thisCircle), int(thisCircle), 10, (255, 0, 0))

		pygame.display.flip()
		print(nPts.value)
