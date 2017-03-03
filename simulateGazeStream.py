"""
To help with debugging/testing, this script will simulate a pupil capture session.

One socket will be listening for incoming requests. When it receives a request for the SUB_PORT, 
it will return the port number assigned to the data streaming port. 

The other socket will be continually streaming data formatted in a way to match how pupil capture
streams gaze data that has been mapped to a defined surface in the scene
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
	m = .5
	std = .05

	# start data streaming
	while True:
		
		# create datapoint
		thisX = np.random.normal(m, std)
		thisY = np.random.normal(m, std)

		# format message
		topic = 'surface'
		msgDict = {b'gaze_on_srf': [{b'norm_pos': [thisX, thisY]}]}

		# send the topic and dictionary
		data_socket.send_string(topic, zmq.SNDMORE)
		data_socket.send(serializer.dumps(msgDict, use_bin_type=True))
		print(msgDict)
		time.sleep(.02)











