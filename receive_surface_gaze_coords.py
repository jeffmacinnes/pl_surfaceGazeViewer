"""
stream gaze coordinates translated to identified surface
"""





# here's a clue:
surface_name = "screen"
while True:
    msg = socket.recv()
    items = msg.split("\n") 
    msg_type = items.pop(0)
    items = dict([i.split(':') for i in items[:-1] ])
    if msg_type == 'Pupil':
        try:
            gaze_on_screen = items["realtime gaze on "+surface_name]
            raw_x,raw_y = map(float,gaze_on_screen[1:-1].split(','))
            
            # smoothing out the gaze so the mouse has smoother movement
            smooth_x += 0.5 * (raw_x-smooth_x)
            smooth_y += 0.5 * (raw_y-smooth_y)