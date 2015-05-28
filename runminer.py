#!/usr/bin/env python

from subprocess import Popen, PIPE
import sys, time, os, signal, numpy
import getopt
import traceback

from logger import Logger
from emmarshal import EthminerMarshal
from gethmarshal import GethMarshal
from inputthread import InputThread
from gethjson import GethJSON

# hammer hexcode 01f528 Mined block block number [maybe not that order]

class StopException(Exception):
    def __init__(self):
        pass

SPEED_MAX_SAMPLE_SIZE = 100

DEFAULTS = {
    'GPU': False,
    'benchmark': False,
    'run-server' : True,
    'geth-server': 'geth',
    'ethminer': 'ethminer',
    'verbose': False,
    'hps-sample-size': 10,
    'debug': False,
    'speed-refresh': 2,
    'threads': None, # Nothing set means don't pass anything to ethminer which is full power
    'geth-rpc':('http://localhost', 8545)
}

OPTIONS = (
    "hGMsvdt:",
    [
        'geth=',
        'ethminer=',
        'threads=',
        'help'
    ]
)

def printUsage():
    print 'runminer.py - Ethereum mining helper script using ethminer and geth.'
    print 'Usage: ./runminer.py [-G] [-M] [-s] [-v] [--geth=] [--ethminer=]'
    print '\t -h, --help \t This help'
    print '\t -G \t Run on the graphics card'
    print '\t -M \t Perform a benchmark test using ethminer'
    print '\t -s \t Don\'t run Geth server before executing ethminer'
    print '\t -v \t Verbose mode (Show every line of output from geth and ethminer)'
    print '\t -t, --threads=   Set the number of CPU/GPU threads to use '
    print '\t    \t\t(Without this flag ethminer will use all available CPU/GPU threads'
    print '   --geth=    indicates the location of the geth binary'
    print '   --ethminer=       indicates the location of the ethminer binary'
    print '\n\nCreated by Cameron Diver  (cameron.diver94@gmail.com)'
    print '    and   Joseph Roberts  (j.baldwin.roberts@gmail.com)'
def getOptions(args):
    config = {}

    try:
        opts, args = getopt.getopt(args, OPTIONS[0], OPTIONS[1])
    except getopt.GetoptError:
        print 'Error parsing input'
        printUsage()
        sys.exit()
        
    for opt, arg in opts:
        if opt == '-G':
            config['GPU'] = True
        elif opt == '-M':
            config['benchmark'] = True
            config['verbose'] = True
            config['run-server'] = False
        elif opt == '-s':
            config['run-server'] = False
        elif opt == '-v':
            config['verbose'] = True
        elif opt == '--geth':
            config['geth-server'] = arg
        elif opt == '--ethminer':
            config['ethminer'] = arg
        elif opt in ('-t', '--threads'):
            config['threads'] = int(arg)
        elif opt in ('-h', '--help'):
            printUsage()
            sys.exit()
        elif opt == '-d':
            config['debug'] = True
    
    # Set any unset values to the default
    for key in DEFAULTS:
        if not key in config:
            config[key] = DEFAULTS[key]

    return config

def turnEchoOff():
    Popen(['stty', '-echo'])

def turnEchoOn():
    Popen(['stty', 'echo'])

def printInputChars(log):
    log.log('info', 'Supported keyboard shortcuts:')
    log.log('info', 'h)  Show this help.\tq)   Quit')
    log.log('info', 'a)  Show accounts')

def handleInput(log, char, json):
    if char == 'q':
        raise KeyboardInterrupt
    elif char == 'h':
        printInputChars(log)
    elif char == 'a':
        accs = json.getAccounts()
        log.log('info', 'Registered Accounts:')
        for idx, acc in enumerate(accs):
            log.log('info', str(idx+1)+'. '+str(acc))

    


config = getOptions(sys.argv[1:])

# Start the logging class before the process so it has somewhere to print to
log = Logger()

inputThread = InputThread()
inputThread.start()

if config['run-server']:
    geth = GethMarshal(config)
    log.log('info', "Running command '%s'" % ' '.join(geth.command))
    geth.runGeth()
    time.sleep(1)

log.log('info', 'Connecting to geth JSON...')
json= GethJSON(config['geth-rpc'])

ethminer = EthminerMarshal(config)

timeCheck = time.time()

try:
    turnEchoOff()
    log.log('info', "Running command '%s'" % ' '.join(ethminer.command))
    
    ethminer.start()
    
    time.sleep(1)
    while True:
        lines = ethminer.getOutput()
        
        for line in lines:
            
            strLine = line[1]
            if line[0] == '':
                log.log('ethminer', strLine.strip())
            #else:
                #log.logDynamic('ethminer', line[0], line[1])

        
        if config['run-server']:
            gethLines = geth.getOutput()
            
            for line in gethLines:
                strLine = line[1]
                if line[0] == '':
                    log.log('geth', line[1])
                else:
                    log.logDynamic('geth', line[0], line[1])

        
        if inputThread.hasChar():
            handleInput(log, inputThread.getChar(), json)

        #if (time.time() - timeCheck) > config['speed-refresh']:
            #if ethminer.gotHPS:
                #log.logDynamic('ethminer', 'SPEEDLINE', ethminer.getSpeedOutput())
            #timeCheck = time.time()

except KeyboardInterrupt:
    log.log('info','Received quit shortcut, stopping processes...')
    log.log('info', 'Please wait to avoid ethereum directory corruption.')

finally:
    
    inputThread.stopEvent.set()
    
    ethminer.process.terminate()
    ethminer.stop()
    
    if config['run-server']:
        geth.killGeth()

    turnEchoOn()
    sys.exit()
    