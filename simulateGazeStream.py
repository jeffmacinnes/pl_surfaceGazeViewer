"""
To help with debugging/testing, this script will simulate a pupil capture session.

One socket will be listening for incoming requests. When it receives a request for the SUB_PORT, 
it will return the port number assigned to the data streaming port. 

The other socket will be continually streaming data formatted in a way to match how pupil capture
streams gaze data that has been mapped to a defined surface in the scene. These mapped points are expressed
as x and y locations normalized with respect to the width and height of the surface. 

For this simulation, the "normalized" gaze points are randomly drawn from a normal distribution with a mean
of .5 (for y), and either .25 or .75 (for x; alternates every few seconds). So in effect, the points streamed will
be shown as two clusters of locations that alternate back and forth across the image. 
"""

import os, sys
import zmq
import time
import numpy as np
import msgpack as serializer
from multiprocessing import Process

# ports:
rep_port = 50020		# listens for requests
data_port = 50040		# streams gaze data


def create_rep_socket(rep_port, data_port):
	""" 
	Will listen for requests on the "rep_port". Whenever a
	request for SUB_PORT arrive, return the port number that 
	data is being streamed over (data_port) 
	"""
	
	# Initialize socket
	context = zmq.Context()
	rep_socket = context.socket(zmq.REP)
	rep_socket.bind('tcp://*:{}'.format(rep_port))

	# listen for requests
	while True:
		message = rep_socket.recv_string()
		if message == 'SUB_PORT':
			print('sending data port: {}'.format(data_port))
			rep_socket.send_string(str(data_port))

def switchPosition(curPosition):
	x1 = .25
	x2 = .75

	if curPosition == x1:
		newPosition = x2
	elif curPosition == x2:
		newPosition = x1

	return newPosition



if __name__ == '__main__':
	
	# set up parent and child sockets
	context = zmq.Context()
	data_socket = context.socket(zmq.PUB)
	data_socket.bind('tcp://*:{}'.format(data_port))

	# initialize req/reply socket on separate thread
	p = Process(target=create_rep_socket, args=(rep_port, data_port))
	p.daemon = True
	p.start()

	# gaze parameters
	x1 = .25
	x2 = .75
	m = .5
	std = .05

	# start data streaming
	startTime = time.time()
	while True:
		
		# create datapoint
		#curTime = time.time() - startTime
		#print(curTime)
		if int(time.time()-startTime) % 2 == 0:
			Xm = x2
		else:
			Xm = x1
		thisX = np.random.normal(Xm, std)
		thisY = np.random.normal(m, std)

		# format message
		topic = 'surface'
		msgDict = {b'gaze_on_srf': [{b'norm_pos': [thisX, thisY]}]}

		# send the topic and dictionary
		data_socket.send_string(topic, zmq.SNDMORE)
		data_socket.send(serializer.dumps(msgDict, use_bin_type=True))
		print(msgDict)
		time.sleep(.02)











