from __future__ import print_function
import zmq
from time import sleep,time


context =  zmq.Context()
socket = context.socket(zmq.REQ)

IP = '127.0.0.1'        # local
#IP = '10.188.94.228'
PORT = '54048'

# set your ip here
socket.connect('tcp://' + IP + ':' + PORT)
t= time()
socket.send_string('t')
print (socket.recv_string())
print ('Round trip command delay:', time()-t)
print ('If you need continous syncing and/or less latency look at pupil_sync.')
sleep(1)
socket.send_string('R')
print (socket.recv_string())
sleep(5)
socket.send_string('r')
print (socket.recv_string())