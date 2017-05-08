# Surface Gaze Viewer

Tool for live visualization of streaming gaze data using [Pupil Labs](http://www.pupil-labs.com) wearable eye-tracker. Gaze points that have been mapped to a surface (e.g. identified using fiducial markers) in the environment are streamed to a remote connection and overlaid onto a static reference image in real-time. 

Note:
Built using Python 2.7.8, and requires Pygame, ZMQ, and OpenCV

![Demo](demo.gif)


## Set-up:
This tool is for situations where a participant is wearing the Pupil Labs eye-tracker, viewing an object in the environment, and you want to visualize their gaze behavior with respect to that object. The object is identified as a "surface" using fiducial markers placed in the environment or some other means. For more info on using fiducial markers to identify surfaces, see [Pupil Labs - Marker Tracking](https://docs.pupil-labs.com/#marker-tracking)

### Quick Start:
`python drawMappedGaze.py host port refImage`

where:

- `host`: IP address of machine running Pupil Capture, streaming the data
- `port`: Port number to communicate over
- `refImage`: Local path to the image file to be used as static reference image (gaze points will be overlaid onto this image)

Once it is running, you can use the following keys to toggle various aspects of the visualization:

- `b` toggle the reference image on/off
- `g` toggle gaze points on/off
- `h` toggle heatmap on/off
- `r` reset all data points
- `t` toggle between showing ALL gaze points, or just recent trace

In addition, if the calibration is off, you can use the `arrow` keys to manually adjust the x and y locations of all incoming datapoints. 


### Testing:
For the purposes of testing/debugging the visualizer without having to run a live Pupil Capture session, there is an additional tool included that will simulate a session and stream fake data.

To run:
`python simulateGazeStream.py`

The port numbers are hardcoded in this script; Make sure you use the same `rep_port` port number when calling `drawMappedGaze.py`

One socket will be listening for incoming requests. When it receives a request for the SUB_PORT, 
it will return the port number assigned to the data streaming port. 

The other socket will be continually streaming data formatted in a way to match how pupil capture
streams gaze data that has been mapped to a defined surface in the scene. These mapped points are expressed
as x and y locations normalized with respect to the width and height of the surface. 

For this simulation, the "normalized" gaze points are randomly drawn from a normal distribution with a mean
of .5 (for y), and either .25 or .75 (for x; alternates every few seconds). So in effect, the points streamed will
be shown as two clusters of locations that alternate back and forth across the image.    








