from __future__ import print_function
import zmq
import time
import random
import numpy as np 

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
	messageData = np.random.rand(2)
	messageData = random.randrange(1,500)
	msgString = '%s %d' % (topic, messageData)
	print('sent %s' % msgString)
	pub_socket.send_string(msgString)
	time.sleep(.5)


