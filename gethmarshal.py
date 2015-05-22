from subprocess import Popen, PIPE
import os, signal, threading


# Important output
# Block synchronisation started
# Mining operation aborted due to sync operation
# imported 256 block(s) (0 queued 0 ignored) in 2.372852125s. #396572 [7b317a5e / c58170d4]
# Starting mining operation (CPU=0 TOT=1)



class GethMarshal(object):
    # TODO: get the location of the geth binary from config file
    def __init__(self, config):
        self.config = config
        self.gethFile = config['geth-server']

        self.command = [
            self.gethFile,
            '--rpccorsdomain',
            'localhost',
            '--rpc'
            # TODO: interface with the javascript console
            #console
        ]
        self.thread = None

        self.gethBuffer = []
        self.running = False
        self.stopRequest = threading.Event()

    def runGeth(self):
        # run the process in another thread
        #print 'Starting '+' '.join(self.command)+'...'
        self.thread = self.GethThread(self.command)
        self.thread.start()
        self.thread.running = True


    def isRunning(self):
        if self.thread is None:
            return False
        return self.thread.running
       


    def getOutputLine(self):
        if self.thread is None:
            raise ValueError('Process has not been started yet')

        self.thread.outputLock.acquire()
        if len(self.thread.output) > 0:
            line = self.thread.output.pop(0).strip()
        else:
            line = None
        self.thread.outputLock.release()

        return line


        

    def killGeth(self):
        self.thread.stopRequest.set()
        self.thread.process.wait()

    class GethThread(threading.Thread):
        def __init__(self, command):
            threading.Thread.__init__(self)
            self.command = command
            self.stopRequest = threading.Event()
            self.output = []
            self.outputLock = threading.Lock()
            self.running = False


        
        def run(self):
            self.process = Popen(self.command, stderr=PIPE)
            while not self.stopRequest.is_set():
                line = self.process.stderr.readline()
                if line == '':
                    print 'Geth has died, exiting...'
                    self.running = False
                    self.join()
                    break                    
                line = self.processLine(line.strip())


                self.outputLock.acquire()
                self.output.append(line)
                self.outputLock.release()
            
        def join(self):
            if self.running:
                self.running = False
                print 'Killing Geth...'
                self.process.wait()

        def processLine(self, line):
            return line[line.find(']')+2:]
                





if __name__ == '__main__':
    path = "/home/cameron/go-ethereum/build/bin/geth"
    gm = GethMarshal(path)
    try:
        gm.runGeth()
        while gm.isRunning():
            line = gm.getOutputLine()
            if line != None:
                print line
    except KeyboardInterrupt:
        print 'Received interrupt, stopping geth...'
        gm.killGeth()


    



