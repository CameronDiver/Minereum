#!/usr/bin/env python

from subprocess import Popen, PIPE
import sys, time, os, signal, numpy
import getopt

# hammer hexcode 01f528 Mined block block number [maybe not that order]

OUTPUT_DELAY = 2
SPEED_MAX_SAMPLE_SIZE = 100

DEFAULTS = {
    'GPU': False,
    'benchmark': False,
    'run-server' : False,
    'geth-server': 'geth',
    'ethminer': 'ethminer',
    'output-poll-time': 2
}

OPTIONS = (
    "hGMst:",
    [
        'geth='
        'ethminer='
        'help'
    ]
)

def printUsage():
    print 'runminer.py - Ethereum mining helper script using ethminer and geth.'
    print 'Usage: ./runminer.py [-G] [-M] [-s] [-t n] [--geth-server=] [--ethminer=]'
    print '\t -G \t Run on the graphics card'
    print '\t -M \t Perform a benchmark test using ethminer'
    print '\t -s \t Run Geth server before executing ethminer'
    print '\t -t n \t Wait n seconds before displaying output (default: 2)'
    print '   --geth-server=    indicates the location of the geth binary'
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
        elif opt == '--geth':
            config['geth-server'] = arg
        elif opt == '--ethminer':
            config['ethminer'] = arg
        elif opt in ('-h', '--help'):
            printUsage()
            sys.exit()
    
    # Set any unset values to the default
    for key in DEFAULTS:
        if not key in config:
            config[key] = DEFAULTS[key]

    return config



def readableHash(hps):
    prefixes = ['h', 'Kh', 'Mh', 'Gh', 'Th', 'Ph']
    prefixIdx = 0
    hpsf = float(hps)
    while hpsf > 1000.0:
        prefixIdx += 1
        hpsf /= 1000.0

    return '%s%s%s' % (str(round(hpsf, 3)), prefixes[prefixIdx], '/s')

def rollingAverage(speedList):
    # TODO: rolling average
    return numpy.mean(speedList)

config = getOptions(sys.argv[1:])

command = [
    config['ethminer']
]

if config['GPU']:
    command.append('-G')
    print 'Running on GPU'
if config['benchmark']:
    print 'Running benchmarking test'
    command.append('-M')

# TODO: run server

print "Running command '%s'" % ' '.join(command)
print config


sys.exit()

process = Popen(command, stderr=PIPE)

timeCheck = 0
HPS = 0

gotHPS = False
gotRollingValues = False

speedList = [0] * SPEED_MAX_SAMPLE_SIZE
speedInsertIdx = 0

try:
    while True:
        line = process.stderr.readline()
        if line == '':
            break

        parts = line.split(' ')
        stripped = filter(lambda x: len(x) != 0, parts)

        if len(stripped) > 9:
            if stripped[9] == 'H/s':
                HPS = int(stripped[8])
                gotHPS = True

                # insert the HPS in the size list
                if speedInsertIdx >= SPEED_MAX_SAMPLE_SIZE:
                    gotRollingValues = True
                    speedInsertIdx = 0
                speedList[speedInsertIdx] = HPS
                speedInsertIdx += 1


        if gotHPS and (time.time() - timeCheck) > OUTPUT_DELAY:
            if gotRollingValues:
                print 'Average Speed: %s' % readableHash(rollingAverage(speedList))
            else:
                print 'Current Speed: %s [Waiting for more results]' % readableHash(HPS)
            timeCheck = time.time()


except KeyboardInterrupt:
    print 'Received keyboard interrupt, stopping processes...'
finally:
    process.wait()