import sys
import zmq
import msgpack as serializer

port = '42000'
IP = '127.0.0.1'

# socket to receive published messages on
context = zmq.Context()
sub_socket = context.socket(zmq.SUB)
sub_socket.connect('tcp://%s:%s' % (IP, port))

# filter topics
try:
	sub_socket.setsockopt(zmq.SUBSCRIBE, 'test')
except TypeError:
	sub_socket.setsockopt_string(zmq.SUBSCRIBE, 'test')

while True:
	topic = sub_socket.recv_string()
	payload = serializer.loads(sub_socket.recv(), encoding='utf-8')
	#msg = sub_socket.recv_string()
	print('topic is:' + topic)
	print(payload)

