#!/usr/bin/env python

from subprocess import Popen, PIPE
import sys, time, os, signal, numpy

# hammer hexcode 01f528 Mined block block number [maybe not that order]

OUTPUT_DELAY = 2
SPEED_MAX_SAMPLE_SIZE = 100

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



command = [
    'ethminer',
]

if len(sys.argv)< 2:
    print 'Running on CPU'
else:
    if sys.argv == '-G':
        print 'Sorry, only -G switch supported'
        sys.exit()
    print 'Running on GPU'
    command.append('-G')

print "Running command '%s'" % ' '.join(command)

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