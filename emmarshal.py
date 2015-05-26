import numpy
from subprocess import Popen, PIPE
import select, os
import re

from Queue import Empty

# utf8 chars
INFO = '\xe2\x84\xb9'

class EthminerMarshal(object):
    def __init__(self, config):
        self.config = config

        self.command = [
            config['ethminer']
        ]

        if config['GPU']:
            self.command.append('-G')
        if config['benchmark']:
            self.command.append('-M')
        if config['threads'] is not None:
            self.command.append('-t')
            self.command.append(str(config['threads']))

        self.hpsSampleSize = config['hps-sample-size']

        self.gotHPS = False
        self.lastHPS = 0

        self.gotRollingValues = False

        self.speedList = [0] * self.hpsSampleSize
        self.speedListIdx = 0

        self.process = None
        # TODO: move this to state
        self.stopped = True

        self.gotDAG = False


        self.state = {
            'connection-problem': False,
            'DAG-loaded': False
        }

        ############# REMOVE AFTER DEBUGGING
        #self.inFile = open('stderr.txt', 'r')

    def start(self):
        self.stopped = False
        self.process = Popen(self.command, stderr=PIPE, stdout=PIPE)
        


    def stop(self):
        if not self.stopped:
            self.stopped = True
            
            self.process.wait()


    def getOutput(self):
        
        lines = self.readStream()
        # simulate a network break
        #import time
        #time.sleep(0.05)
        #lines = [self.inFile.readline()]
        ret = []
        
        for line in lines:
            stripped = self.getStrippedLine(line)
            
            try:
                # TODO: stripped[2:] may be the only thing we're ever interested in
                if self.isJSONProblemLine(stripped):
                    ret.append(('CONNECTLINE', 'Connecting to geth JSON...'))
                    self.state['connection-problem'] = True
                elif self.isLoadingFromHashLibLine(stripped[2:]):
                    if self.state['connection-problem']:
                        ret.append(('/CONNECTLINE', 'Connected.'))
                        self.state['connection-problem'] = False
                elif self.isWorkPackageLine(stripped[2:]):
                    pass
                elif self.isMiningLine(stripped[2:]):
                    self.handleHPS(float(stripped[7]))
                    #ret.append(('SPEEDLINE', self.getSpeedOutput()))
                elif self.isDAGLoadedLine(stripped[2:]):
                    ret.append(('/DAGLINE', ' '.join(stripped[2:])))
                    #self.state['DAG-loaded'] = True
                elif self.isWorkPackageConfirmLine(stripped[2:]):
                    ret.append(('/DAGLINE', ''))#.join(stripped[2:])))
                    self.state['DAG-loaded'] = True
                elif stripped[0] == 'DAG':
                    if not self.state['DAG-loaded']:
                        ret.append(('DAGLINE', ' '.join(stripped[2:])))
                elif self.isInfoLine(stripped):
                    if self.config['verbose'] or self.config['debug']:
                        ret.append(('', ' '.join(stripped[2:])))   
                else:
                    if self.config['verbose'] or self.config['debug']:
                        ret.append(('', ' '.join(stripped)))   

            except IndexError:
                # TODO: implement debug switch
                if self.config['debug']:
                    print "Index error with input ", line
                pass
        
        return ret

    def handleHPS(self, hps):
        self.gotHPS = True
        self.lastHPS = hps
        if self.speedListIdx == self.config['hps-sample-size']:
            self.speedListIdx = 0
            self.gotRollingValues = True
        self.speedList[self.speedListIdx] = hps
        self.speedListIdx += 1

    def isGrabbingDAGLine(self, stripped):
        return stripped[0] == 'Grabbing' and stripped[1] == "DAG" and stipped[2] == "for"

    def isDAGLoadedLine(self, stripped):
        return stripped[0] == 'Full' and stripped[1] == 'DAG' and stripped[2] == 'loaded'

    def isWorkPackageConfirmLine(self, stripped):
        return stripped[0] == 'Got' and stripped[1] == 'work' and stripped[2] == 'package:'

    def isMiningLine(self, stripped):
        return stripped[0] == 'Mining' and stripped[6] == 'H/s'

    def isWorkPackageLine(self, stripped):
        return stripped[0] == 'Getting' and stripped[1] == 'work' and stripped[2] == 'package...'

    def isJSONProblemLine(self, stripped): 
        return stripped[0] == "JSON-RPC" and stripped[1] == "problem."

    def isLoadingFromHashLibLine(self, stripped):
        return stripped[0] == 'Loading' and stripped[2] == 'libethash...'

    def readStream(self):
        lines = []
        reads = [self.process.stdout.fileno(), self.process.stderr.fileno()]
        #reads = [self.process.stderr.fileno()]
        
        ret = select.select(reads, [], [], 0.5)
        
        # TODO: these read calls may not return the whole line which will
        # mess up the parsing stage so check this
        if self.process.stderr.fileno() in ret[0]:
        
            #line = self.process.stderr.readline()    
            line = os.read(self.process.stderr.fileno(), 2048)
        
            lines.append(line)

        

        if self.process.stdout.fileno() in ret[0]:
            #line = self.process.stdout.readline()
            line = os.read(self.process.stdout.fileno(), 2048)
            lines.append(line)
        
        return lines

    def running(self):
        # not sure if this works...
        return self.process.poll()


    def getStrippedLine(self, line):
        parts = line.split(' ')

        stripped = [self.stripBashColours(piece.strip()) for piece in parts 
            if self.stripBashColours(piece.strip()) != '']
        return stripped
        

    def getSpeedOutput(self):
        if self.gotRollingValues:
            return 'Average Speed: %s'% self.readableHash(numpy.mean(self.speedList))
        else:
            return 'Current Speed: %s\t[Waiting for more results]' % self.readableHash(self.lastHPS)


    def readableHash(self, hps):
        prefixes = ['', 'K', 'M', 'G', 'T', 'P']
        prefixIdx = 0
        hpsf = float(hps)
        while hpsf > 1000.0:
            prefixIdx += 1
            hpsf /= 1000.0
        return '%s%s%s' % (str(round(hpsf, 3)), prefixes[prefixIdx], 'H/s')

    def stripBashColours(self, str):
        str2 = re.sub(r'\x1b[^m]*m', '', str)
        return re.sub('\[.*?;.*?m', '', str2)

    def isInfoLine(self, stripped):
        if stripped[0] == INFO:
            return True
        return False

    def handleDAGLine(self, stripped):
        pass
        

        







