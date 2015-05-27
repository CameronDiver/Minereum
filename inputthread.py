import sys
import threading
import Queue
import select
import time

# Get a single character from the terminal, unix only
class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
getch = _GetchUnix


class InputThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)

        self.stopEvent = threading.Event()
        self.chars = Queue.Queue()


    def run(self):
        while not self.stopEvent.isSet():
            #reads = [sys.stdin.fileno()]
            #ret = select.select(reads, [], [], 0)
            #print ret
            #if sys.stdin.fileno() in ret[0]:
            c = getch().__call__()
            #c = sys.stdin.read(1)
            self.chars.put(c)
        #time.sleep(1)

    def hasChar(self):
        return not self.chars.empty()

    def getChar(self):
        return self.chars.get()
