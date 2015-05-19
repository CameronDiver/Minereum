#!/usr/bin/env python

from subprocess import Popen, PIPE
import sys, time, os, signal

# hammer hexcode 01f528 Mined block block number [maybe not that order]

OUTPUT_DELAY = 2


def readableHash(hps):
    prefixes = ['h', 'Kh', 'Mh', 'Gh', 'Th', 'Ph']
    prefixIdx = 0
    hpsf = float(hps)
    while hpsf > 1000.0:
        prefixIdx += 1
        hpsf /= 1000.0

    return '%s%s%s' % (str(round(hpsf, 3)), prefixes[prefixIdx], '/s')


command = [
    'ethminer',
]

if len(sys.argv)< 2:
    print 'Runing on CPU'
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

        if gotHPS and (time.time() - timeCheck) > OUTPUT_DELAY:
            print 'Current Speed: %s' % readableHash(HPS)
            timeCheck = time.time()

except KeyboardInterrupt:
    print 'Received keyboard interrupt, stopping processes...'
    os.kill(process.pid, signal.SIGINT)
finally:
    process.wait()