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
            '--rpc',
            '--autodag'
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
       


    def getOutputLines(self):
        if self.thread is None:
            raise ValueError('Process has not been started yet')
        lines = []
        self.thread.outputLock.acquire()
        while len(self.thread.output) > 0:
            line = self.thread.output.pop(0).strip()
            lines.append(line)
        self.thread.outputLock.release()

        return lines

    def getOutput(self):
        lines = self.getOutputLines()

        retLines = []
        for line in lines:
            stripped = filter(lambda a: a != '', line.split(' '))
            if self.isStartMiningOperation(stripped):
                retLines.append(' '.join(stripped))
            elif self.isMiningAbortedLine(stripped):
                retLines.append(' '.join(stripped))
            elif self.isProtocolVersionLine(stripped):
            	retLines.append(' '.join(stripped))
            elif self.isBlockChainVersionLine(stripped):
            	retLines.append(' '.join(stripped))
            elif self.isStartingServerLine(stripped):
            	retLines.append(' '.join(stripped))
            else:
                if self.config['verbose'] or self.config['debug']:
                    retLines.append(' '.join(stripped))

        return retLines



    def isStartMiningOperation(self, stripped):
        # Starting mining operation (CPU=0 TOT=1)
        return stripped[0] == 'Starting' and stripped[1] == 'mining' and stripped[2] == 'operation'

    def isMiningAbortedLine(self, stripped):
        #  Mining operation aborted
        return stripped[0] == "Mining" and stripped[1] == "operation" and stripped[2] == 'aborted'

    def isProtocolVersionLine(self, stripped):
    	# Protocol Version: 60, Network Id: 0
    	return stripped[0] == "Protocol" and stripped[1] == "Version:"

    def isBlockChainVersionLine(self, stripped):
        #  Blockchain DB Version: 2
        return stripped[0] == "Blockchain" and stripped[1] == "DB" and stripped[2] == 'Version:'

    def isStartingServerLine(self, stripped):
        #  Starting Server
        return stripped[0] == "Starting" and stripped[1] == "Server"
        

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
            try:
                self.process = Popen(self.command, stderr=PIPE)
                self.running = True
            except Exception:
                self.running = False
                return

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
    config = {
        'geth-server': "/home/cameron/go-ethereum/build/bin/geth"
    }
    gm = GethMarshal(config)
    try:
        gm.runGeth()
        while gm.isRunning():
            line = gm.getOutputLine()
            if line != None:
                print line
    except KeyboardInterrupt:
        print 'Received interrupt, stopping geth...'
        gm.killGeth()


    



