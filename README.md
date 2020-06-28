# parallelImageProcessingWithPythonAndOpenCV
Demos for parallelization with processes and concurrency with threads for image processing with Python and OpenCV

This is a README file.

Author: Santiago Maraggi
Licence: MIT (free to use, modify, distribute, etc.)
Contact: smaraggi [at] gmail [dot] com

If these examples were useful for your project, any mention is welcome.

Multithreading solution is faster for the program to startup, and it 
would be  advisable for simple projects, when there is not very heavy 
load on processing algorithms and you want to keep your program simple
within a single process.

Multiprocessing solution spawns multiple processes and IPC mechanisms, 
instead of threads within the main process. This solution can take better 
advantage from parallel architectures (which are ubiquitous today), however 
the program may take longer to start, due to process initialization overhead.

Processes rely on the operating system capabilities. Python reports that
some methods work differently in different platforms. This solution would
work equally in all platforms, as far as I could read and test, if you find
different behaviour in different platforms, please, let me know!

Multithreading is optimal to keep an application responsive, attending
many tasks at once (mostly avoiding iddle times due to long input/output 
delays) within a single process.

Multiprocessing allows the program to use multiple cores from the CPU, 
as long as the OS can support these functionalities.

Both examples run smoothly on my computer. The synchronization is provided
mostly by the interchange queues for the video frames, although some lock is 
also used. 

Basically, the proposed solutions separate camera frame capture, video frame 
processing and video frame display, making possible to process many frames
at once, wether with processes and parallelism or threads and concurrency.

These kind of implementations would boost your overall "frames per second" (FPS)
for any project compared with linear single-threaded processing.

Have a happy multithreading/multiprocessing!