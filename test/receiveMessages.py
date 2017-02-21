import sys
import zmq

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
	msg = sub_socket.recv_string()
	print(msg)

