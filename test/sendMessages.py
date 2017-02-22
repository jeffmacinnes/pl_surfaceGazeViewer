from __future__ import print_function
import zmq
import time
import random
import numpy as np 
import msgpack as serializer

port = '42000'

# let the OS choose the IP and PORT
ipc_sub_url = 'tcp://*:*'
ipc_push_url = 'tcp://*:*'

# starting communication threads
zmq_ctx = zmq.Context()
pub_socket = zmq_ctx.socket(zmq.PUB)
pub_socket.bind("tcp://*:%s" % port)


# send messages
while True:
	topic = 'test'
	thisX = np.random.rand()
	thisY = np.random.rand()
	testDict = {'gaze':(thisX, thisY)}
	pub_socket.send_string(topic, zmq.SNDMORE)
	pub_socket.send(serializer.dumps(testDict, use_bin_type=True))
	print(testDict)
	time.sleep(.02)


