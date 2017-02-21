"""
Stream gaze coordinate data using zmq
"""
from __future__ import print_function
import zmq
import msgpack as serializer

IP = '10.188.94.130'
#IP = '127.0.0.1'
PORT = '52420'

#network setup, create request to send to the pupil IPC
context = zmq.Context()
requester = context.socket(zmq.REQ)
requester.connect('tcp://%s:%s' %(IP, PORT))

# ask for the subport
requester.send_string('SUB_PORT')
sub_port = requester.recv_string()
print('received sub port:' + sub_port)

# open a new socket on this port and subscribe
sub = context.socket(zmq.SUB)
sub.connect('tcp://%s:%s' %(IP, sub_port))

# look for specific topics
try:
	sub.setsockopt(zmq.SUBSCRIBE, 'surface')
except TypeError:
	sub.setsockopt_string(zmq.SUBSCRIBE, 'surface')


# start listening
while True:
	topic, msg = sub.recv_multipart()
	message = serializer.loads(msg)		# turns to dict
	try:
		for d in message[b'gaze_on_srf']:
			print(d[b'norm_pos'])
		print('\n'*2)
	except:
		pass
	
