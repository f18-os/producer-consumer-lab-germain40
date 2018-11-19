#!/usr/bin/env python3

import threading
import cv2
import numpy as np
import base64
import queue

class Q:
    def __init__(self, initArray = []):
        self.a = []
        self.a = [x for x in initArray]
    def put(self, item):
        self.a.append(item)
    def get(self):
        a = self.a
        item = a[0]
        del a[0]
        return item
    def __repr__(self):
        return "Q(%s)" % self.a


def extractFrames(fileName, outputBuffer):
    # Initialize frame count 
    count = 0

    # open video file
    vidcap = cv2.VideoCapture(fileName)

    # read first image
    success,image = vidcap.read()
    
    print("Reading frame {} {} ".format(count, success))
    while success:
        # get a jpg encoded frame
        success, jpgImage = cv2.imencode('.jpg', image)

        #encode the frame as base 64 to make debugging easier
        jpgAsText = base64.b64encode(jpgImage)

        # add the frame to the buffer and use semaphores
        empty_Count.acquire()
        outputBuffer.put(jpgAsText)
        fill_Count.release()
       
        success,image = vidcap.read()
        print('Reading frame {} {}'.format(count, success))
        count += 1

    print("Frame extraction complete")

def convert(inputBuffer, outputBuffer):
    count = 0
    while True:
        # get and use semaphores from extraction
        fill_Count.acquire()
        frameAsText = inputBuffer.get()
        empty_Count.release()

        jpgRawImage = base64.b64decode(frameAsText)
        jpgImage = np.asarray(bytearray(jpgRawImage), dtype=np.uint8)
        img = cv2.imdecode(jpgImage, cv2.IMREAD_UNCHANGED)
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        success, jpgImage = cv2.imencode('.jpg', gray_img) 
        jpgAsText = base64.b64encode(jpgImage)

        # put and use semaphores for conversion
        empty_Count2.acquire()
        outputBuffer.put(jpgAsText)
        fill_Count2.release()

        print('Converting Frame {}'.format(count))
        count += 1
    print("Conversion complete")

def displayFrames(inputBuffer):
    # initialize frame count
    count = 0

    # go through each frame in the buffer until the buffer is empty
    while True:
        # get the next frame and use semaphores for conversion
        fill_Count2.acquire()
        frameAsText = inputBuffer.get()
        empty_Count2.release()

        # decode the frame 
        jpgRawImage = base64.b64decode(frameAsText)

        # convert the raw frame to a numpy array
        jpgImage = np.asarray(bytearray(jpgRawImage), dtype=np.uint8)
        
        # get a jpg encoded frame
        img = cv2.imdecode( jpgImage ,cv2.IMREAD_UNCHANGED)

        print("Displaying frame {}".format(count))        

        # display the image in a window called "video" and wait 42ms
        # before displaying the next frame
        cv2.imshow("Video", img)
        if cv2.waitKey(42) and 0xFF == ord("q"):
            break

        count += 1

    print("Finished displaying all frames")
    # cleanup the windows
    cv2.destroyAllWindows()

# filename of clip to load
filename = 'clip.mp4'

buf = 10
# extractionQueue semaphores!
fill_Count = threading.Semaphore(0)
empty_Count = threading.Semaphore(buf)

# convertQueue semaphores!
fill_Count2 = threading.Semaphore(0)
empty_Count2 = threading.Semaphore(buf)

# shared queue  
extractionQueue = Q()
convertQueue = Q()

# extract the frames
# extractFrames(filename,extractionQueue)
ext = threading.Thread(target=extractFrames, args=(filename, extractionQueue))
# convert frames
# convert(extractionQueue, convertQueue)
con = threading.Thread(target=convert, args=(extractionQueue, convertQueue))
# display the frames
# displayFrames(convertQueue)
dis = threading.Thread(target=displayFrames, args=(convertQueue,))

ext.start()
con.start()
dis.start()