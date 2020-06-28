# Python 3 - OpenCV camera reading and multiprocessing example
# Author: Santiago Maraggi
# Contact: smaraggi@gmail.com

# Imports
import cv2
import time
import queue # for queue exception import purposes
import threading # camera read will use an individual thread in the main process
from multiprocessing import Process, Queue, Value, Lock

# simulated task execution time for each process in seconds
# let's put on a very heavy weight load... 0.5 seconds of work processing per frame per process
individualProcessSimulatedWorkExecutionTime = 0.5

# frame queues size
frameQueueSize = 20

# process quantity
workingProcessesAmount = 16 # at 30 FPS, with 0.5 seconds delay, during the processing of 1 frame, 15 more frames will be read

# list of active processes
workingProcesses = []

# capturing frames unique thread 
frameCapturingThread = None

# Frame Queue for displaying frames: put after processing to be rendered by the GUI (main) process
processedFramesIntermediateQueue = Queue(maxsize=frameQueueSize)

# Frame Queue for frames directly captured from the camera and to be processed
capturedRawFramesIntermediateQueue = Queue(maxsize=frameQueueSize)

# global application state
stateWorking = Value('d', 1.0) # 1 means "True" in this program, 0 False...

# Lock to contabilize frames per second overall
fps_counter_lock = Lock()

# Variable to count processed frames
fps_count = Value('d', 0.0)

# time count for each 100 processed frames
frame_100_count_elapsed_time_seconds = Value('d', 0.0)

def makeIntro():
    print("######################################################################")
    print("Python 3 - OpenCV camera reading and multiprocessing processing example")
    print("Author: Santiago Maraggi")
    print("Contact: smaraggi@gmail.com")
    print("######################################################################")
    print("This program simulates a hard work on video frames, using multiprocessing to avoid loosing frames in the way")
    print("Multiple processes can have a better use of parallel architectures, using multiple cores, than simple multithreading")
    print("Current program parameters are the following:")
    print("Frame Queue Size (both for camera read and processed frames queues): ", frameQueueSize)
    print("Working processes amount (appart from the camera read unique thread within the main application process): ", workingProcessesAmount)
    print("Camera frames reading is a thread in order to access opencv camera more easily, it should not be a big deal")
    print("Working processes however are modeled as processes in order to enable parallel execution")
    print("Working process simulated individual execution time per frame task run: ", individualProcessSimulatedWorkExecutionTime, " seconds")
    print("To end the program, put the focus on the video window and press any key")
    print("######################################################################")
    print("Notes:")
    print("1) Be aware that sliding the terminal output may interfere with program execution times")
    print("2) The goal would be to keep the processing and display FPS similar to the camera capture FPS, but with some latency")
    print("     ...the latency would be unavoidable, given the execution time of the work performed by working processes for each frame")
    print("     ...a good experiment would be to play with the parameter values (queue sizes, work load execution time, working processes)...")
    print("         ...and see the results")
    print("3) For the proposed initial values (frameQueueSize=20, workingprocessesAmount=16, individualProcessSimulatedWorkExecutionTime=0.5)")
    print("     ...the logic is that at 30 FPS, if the working task takes 0.5 seconds, then 15 other frames would already be read")
    print("         ... so other 15 processes are ready for that. Fluctuations may happen, but that is the logic behind the values")
    print("######################################################################")
    print("Process setup at program start is slower than with multithreading (see my equivalent multithreading example)")
    print("However multiprocess execution should run faster in multicore systems, if the platform supports parallel execution")
    print("######################################################################")
    print("If this file was useful to you, please ley me know, credit will always be thanked properly")
    print("Have a Happy multiPROCESSING!")
    print("######################################################################")


# Empty Captured Frame Queues Pending from processing to video stream
# Note that if other processes / threads are writing elements to the queues, empty may not leave them "empty"
def emptyQueues(capturedRawFramesIntermediateQueue, processedFramesIntermediateQueue):
    while (capturedRawFramesIntermediateQueue.qsize() > 0): capturedRawFramesIntermediateQueue.get_nowait()
    while (processedFramesIntermediateQueue.qsize() > 0): processedFramesIntermediateQueue.get_nowait()

# Function to determine if all the queues where properly processed
# Note that if other processes / threads are writing elements to the queues, this would not be a reliable value
def queuesEmpty(capturedRawFramesIntermediateQueue, processedFramesIntermediateQueue):
    return (capturedRawFramesIntermediateQueue.qsize() == 0 and processedFramesIntermediateQueue.qsize() == 0)

# Frame capture function. Runs on an individual thread, puts raw frames into an intermediate queue
def frameCapturingFunction(capturedRawFramesIntermediateQueue, stateWorking):
    
    # setup camera. The camera capture process initializes the camera directly, not the master thread
    cap = cv2.VideoCapture(0) # regular OpenCV camera
    
    while (stateWorking.value == 1.0):
        
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
    cap.release() # release standard OpenCV camera

def workingProcessFunction(capturedRawFramesIntermediateQueue, processedFramesIntermediateQueue, fps_counter_lock, fps_count, frame_100_count_elapsed_time_seconds, stateWorking):
    print("Working process starting")

    while (stateWorking.value == 1.0):
    
        #Obtain frames which were already read in a separate process
        if (capturedRawFramesIntermediateQueue.qsize() > 0):
            try:
                frame = capturedRawFramesIntermediateQueue.get_nowait()
                # print("This process is processing a frame!") # beware, these calls consume process time...
                
                # Here the "frame" should be processed...
                # call to an interesting function...
                # processIndividualFrame(frame)
                # let's simulate some processing with a wait function...
                time.sleep(individualProcessSimulatedWorkExecutionTime)
                
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
                fps_count.value += 1
                if (fps_count.value > 100):
                    actual_time = time.time()
                    delta_time = actual_time - frame_100_count_elapsed_time_seconds.value
                    frame_100_count_elapsed_time_seconds.value = actual_time
                    # this print is less critical, as it is called once in a while
                    print("Processed 100 frames in ", frame_100_count_elapsed_time_seconds.value, "seconds. FPS is ", 100 / delta_time)
                    fps_count.value = 0
                fps_counter_lock.release()
                
            except queue.Empty:
                # all items from camera captured frames queue have been processed, return to start to check for new frames
                # this happens when some processes are iddle while some others work, it would be desireable
                # overload happens when all working processes are working and no one is free to take a new read frame
                pass

    # consume eventual remaining read frames to discard them
    while (capturedRawFramesIntermediateQueue.qsize() > 0):
        try:
            frame = capturedRawFramesIntermediateQueue.get_nowait()
        except queue.Empty:
            pass
            
    print("Working process stopping")
    
    # for multiprocessing, remaining written elements into a queue might block child process join with the parent process
    # processedFramesIntermediateQueue.cancel_join_thread() # if frames remain to be displayed, don't let those block this process join to master process
    # capturedRawFramesIntermediateQueue.cancel_join_thread() # same as above

# start reading camera process and working processes
def startWorking():
    global stateWorking
    global fps_count
    global frame_100_count_elapsed_time_seconds
    global capturedRawFramesIntermediateQueue
    global processedFramesIntermediateQueue

    # clear old frames, in case there are some...
    emptyQueues(capturedRawFramesIntermediateQueue, processedFramesIntermediateQueue)

    frame_100_count_elapsed_time_seconds.value = time.time()
    
    global frameCapturingThread
    frameCapturingThread = threading.Thread(target=frameCapturingFunction, args=(capturedRawFramesIntermediateQueue, stateWorking))
    frameCapturingThread.start()
    
    global workingProcesses
    for x in range (0, workingProcessesAmount):
        new_process = Process(target=workingProcessFunction, args=(capturedRawFramesIntermediateQueue, processedFramesIntermediateQueue, fps_counter_lock, fps_count, frame_100_count_elapsed_time_seconds, stateWorking))
        new_process.start()
        workingProcesses.append(new_process)

# stop reading frames from the capera
def stopReadingFrames():
    global stateWorking
    stateWorking.value = 0.0 # 0.0 for False, this is the shared variable that signals all processes to finish, no need to lock the variable to write this value here, each process will end at its pace
    
    global frameCapturingThread
    frameCapturingThread.join() # join reading frames from camera process
    
    print ("Joined camera capture process")

def stopWorkingProcesses():
    global workingProcesses
    for process in workingProcesses:
        process.terminate()
        process.join() # join each working process
        print ("Joined a working process")
    workingProcesses.clear() # clear process list (all are finished)
    print ("Joined all working processes")
    print("Stopped work")

def cleanUp():
    # ----
    # To close windows, these calls differ in linux or windows. This is the only OS system dependance I found
    # if (cv2.getWindowProperty("Display_Window", cv2.WND_PROP_OPENGL) != -1): # this is for Linux windows systems only
    if (cv2.getWindowProperty("Display_Window", 0) != -1): # Only for Windows window systems only
        cv2.destroyWindow("Display_Window")
    # ----
    cv2.destroyAllWindows()
    
def showFrameInWindow(frame, window_name, x, y):
     cv2.namedWindow(window_name)
     cv2.moveWindow(window_name,x , y)
     cv2.imshow(window_name, frame)
    
# Main function ---------------------------------------------------

if __name__ == '__main__':
    makeIntro()
    
    endProgram = False
    programTerminated = False
    
    startWorking()
    
    while (programTerminated == False):
        try:
            displayFrame = processedFramesIntermediateQueue.get_nowait()
            # Note that GUI elements should be handled in the main process...
            showFrameInWindow(displayFrame, "Display_Window", 50, 50)
        except queue.Empty:
            # nothing special, keep running the program
            pass
        
        k = cv2.waitKey(1) # required for the GUI to be responsive when showing frames
        
        if k !=- 1:    # any key to stop
            print("Finishing Program")
            stopReadingFrames()
            endProgram = True
        
        if (endProgram == True and processedFramesIntermediateQueue.qsize() == 0):
            programTerminated = True
            
    stopWorkingProcesses()
    # stopWorking()
    time.sleep(1) # so you can read the last messages
    print("Cleaning Up")
    cleanUp()
    print("All done")