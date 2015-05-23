#!/usr/bin/env python

from subprocess import Popen, PIPE
import sys, time, os, signal, numpy
import getopt
import traceback
from logger import Logger
from emmarshal import EthminerMarshal
from gethmarshal import GethMarshal

# hammer hexcode 01f528 Mined block block number [maybe not that order]

OUTPUT_DELAY = 2
SPEED_MAX_SAMPLE_SIZE = 100

DEFAULTS = {
    'GPU': False,
    'benchmark': False,
    'run-server' : False,
    'geth-server': 'geth',
    'ethminer': 'ethminer',
    'verbose': False,
    'hps-sample-size': 10,
    'debug': False
}

OPTIONS = (
    "hGMsvd",
    [
        'geth=',
        'ethminer=',
        'help'
    ]
)

def printUsage():
    print 'runminer.py - Ethereum mining helper script using ethminer and geth.'
    print 'Usage: ./runminer.py [-G] [-M] [-s] [-v] [--geth=] [--ethminer=]'
    print '\t -h, --help \t This help'
    print '\t -G \t Run on the graphics card'
    print '\t -M \t Perform a benchmark test using ethminer'
    print '\t -s \t Run Geth server before executing ethminer'
    print '\t -v \t Verbose mode (Show every line of output from geth and ethminer)'
    print '   --geth=    indicates the location of the geth binary'
    print '   --ethminer=       indicates the location of the ethminer binary'

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
        elif opt == '-s':
            config['run-server'] = True
        elif opt == '-t':
            config['output-poll-time'] = int(arg)
        elif opt == '-v':
            config['verbose'] = True
        elif opt == '--geth':
            config['geth-server'] = arg
        elif opt == '--ethminer':
            config['ethminer'] = arg
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

config = getOptions(sys.argv[1:])

# Start the logging class before the process so it has somewhere to print to
log = Logger()
log.addSrcColour('ethminer', 'bold-blue')
log.addSrcColour('geth', 'bold-red')
log.addSrcColour('time', 'bg-green')
log.addSrcColour('info', 'bold-green')


if config['run-server']:
    geth = GethMarshal(config)
    log.log('info', "Running command '%s'" % ' '.join(geth.command))
    geth.runGeth()


ethminer = EthminerMarshal(config)

lastOutputTime = time.time()

try:
    log.log('info', "Running command '%s'" % ' '.join(ethminer.command))
    ethminer.start()
    time.sleep(1)
    while True:
        
        if config['run-server']:
            lines = []
            line = geth.getOutputLine()
            while line != None:
                lines.append(line)
                line = geth.getOutputLine()
            
            for line in lines:
                if config['verbose']:
                    if line != None:
                        log.log('geth', line)


        lines = ethminer.getOutput()
        for line in lines:
            strLine = line[1]
            if line[0] == '':
                log.log('ethminer', strLine.strip())
            else:
                log.logDynamic('ethminer', line[0], line[1])

except KeyboardInterrupt:
    print 'Received keyboard interrupt, stopping processes...'
except:
    print traceback.format_exc()

finally:
    if config['run-server']:
        geth.killGeth()
    ethminer.stop()
    