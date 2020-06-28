# Python 3 - OpenCV camera reading and multithreading processing example
# Author: Santiago Maraggi
# Contact: smaraggi@gmail.com

# Imports
import cv2
import time
import threading
import queue

# simulated task execution time for each thread in seconds
# let's put on a very heavy weight load... 0.5 seconds of work processing per frame per thread
individualThreadSimulatedWorkExecutionTime = 0.5

# frame queues size
frameQueueSize = 20

# thread quantity
workingThreadsAmount = 16 # at 30 FPS, with 0.5 seconds delay, during the processing of 1 frame, 15 more frames will be read

# list of active threads
workingThreads = []

# capturing frames unique thread 
frameCapturingThread = None

# Frame Queue for displaying frames: put after processing to be rendered by the GUI (main) thread
processedFramesIntermediateQueue = queue.Queue(maxsize=frameQueueSize)

# Frame Queue for frames directly captured from the camera and to be processed
capturedRawFramesIntermediateQueue = queue.Queue(maxsize=frameQueueSize)

# global application state
stateWorking = True

# setup camera
cap = cv2.VideoCapture(0) # regular OpenCV camera
target_framerate = 30

# Lock to contabilize frames per second overall
fps_counter_lock = threading.Lock()

# Variable to count processed frames
fps_count = 0

# time count for each 100 processed frames
frame_100_count_elapsed_time_seconds = 0

def makeIntro():
    print("######################################################################")
    print("Python 3 - OpenCV camera reading and multithreading processing example")
    print("Author: Santiago Maraggi")
    print("Contact: smaraggi@gmail.com")
    print("######################################################################")
    print("This program simulates a hard work on video frames, using multithreading to avoid loosing frames in the way")
    print("Current program parameters are the following:")
    print("Frame Queue Size (both for camera read and processed frames queues: ", frameQueueSize)
    print("Working thread amount (appart from the camera read thread and the main application thread): ", workingThreadsAmount)
    print("Working thread simulated individual execution time per frame task run: ", individualThreadSimulatedWorkExecutionTime, " seconds")
    print("To end the program, put the focus on the video window and press any key")
    print("######################################################################")
    print("Notes:")
    print("1) Be aware that sliding the terminal output may interfere with program execution times")
    print("2) The goal would be to keep the processing and display FPS similar to the camera capture FPS, but with some latency")
    print("     ...the latency would be unavoidable, given the execution time of the work performed by working threads for each frame")
    print("     ...a good experiment would be to play with the parameter values (queue sizes, work load execution time, working threads)...")
    print("         ...and see the results")
    print("3) For the proposed initial values (frameQueueSize=20, workingThreadsAmount=16, individualThreadSimulatedWorkExecutionTime=0.5)")
    print("     ...the logic is that at 30 FPS, if the working task takes 0.5 seconds, then 15 other frames would already be read")
    print("         ... so other 15 threads are ready for that. Fluctuations may happen, but that is the logic behind the values")
    print("######################################################################")
    print("If this file was useful to you, please ley me know, credit will always be thanked properly")
    print("Have a Happy multithreading!")
    print("######################################################################")


# Empty Captured Frame Queues Pending from processing to video stream
def emptyQueues():
    global capturedRawFramesIntermediateQueue
    global processedFramesIntermediateQueue
    while (capturedRawFramesIntermediateQueue.qsize() > 0): capturedRawFramesIntermediateQueue.get_nowait()
    while (processedFramesIntermediateQueue.qsize() > 0): processedFramesIntermediateQueue.get_nowait()

# Function to determine if all the queues where properly processed
def queuesEmpty():
    return (capturedRawFramesIntermediateQueue.qsize() == 0 and processedFramesIntermediateQueue.qsize() == 0)

# Frame capture function. Runs on an individual thread, puts raw frames into an intermediate queue
def frameCapturingFunction():
    global capturedRawFramesIntermediateQueue
    global cap
    while (stateWorking == True): # no need to use global keyworkd to read only a variable
        
        # read from camera
        _, frame = cap.read() #I/O limiting operation
        
        try:
            capturedRawFramesIntermediateQueue.put_nowait(frame)
        except queue.Full:
            # TODO: notify client application that frames are being missed because overload
            # This is effective frame loss due to system work overload
            print ("Dropping frames due to full intermediate queue.")
            print ("Consider note 1) of the program intro or modifying program parameters")

    print ("Finished capturing frames")

def workingThreadFunction():
    print("Working thread starting")
    global capturedRawFramesIntermediateQueue
    global processedFramesIntermediateQueue
    global fps_counter_lock
    global fps_count
    global frame_100_count_elapsed_time_seconds
    global stateWorking

    while (stateWorking == True):
    
        #Obtain frames which were already read in a separate thread
        if (capturedRawFramesIntermediateQueue.qsize() > 0):
            try:
                frame = capturedRawFramesIntermediateQueue.get_nowait()
                # print("This thread is processing a frame!") # beware, these calls consume thread time...
                
                # Here the "frame" should be processed...
                # call to an interesting function...
                # processIndividualFrame(frame)
                # let's simulate some processing with a wait function...
                time.sleep(individualThreadSimulatedWorkExecutionTime)
                
                # if display is enabled, send the frame to the display pipeline
                # dislplay frames order will be FIFO with processing pipeline, which might in some cases differ with the camera input order
                # however the approximation might be reasonable, as the processing pipeline is also FIFO with the camera input
                # regardles of a possible processing delay in a specific frame
                # this could vary with different FPS speeds, processing speeds, algorithm workloads and intended display FPS
                if (not processedFramesIntermediateQueue.full()): # this query could be ignored with the put_nowait below
                    try:
                        processedFramesIntermediateQueue.put_nowait(frame)
                    except queue.Full:
                        # video display frame queue is full, ignore this frame
                        pass

                # count processed frame and show each 100 frames
                # we ignore if display queue was full or not, the important thing is that the frame was processed
                fps_counter_lock.acquire()
                fps_count = fps_count + 1
                if (fps_count > 100):
                    actual_time = time.time()
                    delta_time = actual_time - frame_100_count_elapsed_time_seconds
                    frame_100_count_elapsed_time_seconds = actual_time
                    # this print is less critical, as it is called once in a while
                    print("Processed 100 frames in ", frame_100_count_elapsed_time_seconds, "seconds. FPS is ", 100 / delta_time)
                    fps_count = 0
                fps_counter_lock.release()
                
            except queue.Empty:
                # all items from camera captured frames queue have been processed, return to start to check for new frames
                # this happens when some threads are iddle while some others work, it would be desireable
                # overload happens when all working threads are working and no one is free to take a new read frame
                pass

    print("Working thread stopping")

# start reading camera thread and processing working threads
def startWorking():
    global stateWorking
    global fps_count
    global frame_100_count_elapsed_time_seconds

    stateWorking = True

    # clear old frames, in case there are some...
    emptyQueues()

    fps_count = 0
    frame_100_count_elapsed_time_seconds = time.time()
    
    global frameCapturingThread 
    frameCapturingThread = threading.Thread(target=frameCapturingFunction, args=())
    frameCapturingThread.start()
    
    global workingThreads
    for x in range (0, workingThreadsAmount):
        new_thread = threading.Thread(target=workingThreadFunction, args=())
        new_thread.start()
        workingThreads.append(new_thread)

# stop camera reading frame and processing working threads
def stopWorking():
    global stateWorking
    stateWorking = False # this is the shared variable that signals all threads to finish
    
    global frameCapturingThread
    frameCapturingThread.join() # join reading frame
    
    global workingThreads 
    for thread in workingThreads:
        thread.join() # join each working thread
    workingThreads.clear() # clear thread list (all are finished)
    
    print("Emptying queues")
    # empty frames from queues
    emptyQueues()
    
    print("Stopped work")
    
def cleanUp():
    # ----
    # To close windows, these calls differ in linux or windows. This is the only OS system dependance I found
    if (cv2.getWindowProperty("Display_Window", cv2.WND_PROP_OPENGL) != -1): # this is for Linux windows systems only
    # if (cv2.getWindowProperty("Display_Window", 0) != -1): # Only for Windows window systems only
        cv2.destroyWindow("Display_Window")
    # ----
    cap.release() # release standard OpenCV camera
    cv2.destroyAllWindows()
    
def showFrameInWindow(frame, window_name, x, y):
     cv2.namedWindow(window_name)
     cv2.moveWindow(window_name,x , y)
     cv2.imshow(window_name, frame)
    
# Main function ---------------------------------------------------
makeIntro()

endProgram = False

startWorking()

while (endProgram == False):
    try:
        displayFrame = processedFramesIntermediateQueue.get_nowait()
        # Note that GUI elements should be handled in the main thread...
        showFrameInWindow(displayFrame, "Display_Window", 50, 50)
    except queue.Empty:
        # nothing special, keep running the program
        pass
    
    k = cv2.waitKey(1) # required for the GUI to be responsive when showing frames
    
    if k !=- 1:    # any key to stop
        print("Finishing Program")
        endProgram = True
        
stopWorking()
time.sleep(1) # so you can read the last messages
cleanUp()