from subprocess import Popen, PIPE
import sys, time

# ['\x1b[94m', 
#   '\xe2\x84\xb9', 
#   '\x1b[35m15:47:28\x1b[0m\x1b[30m|\x1b[34methminer\x1b[0m',
#   'Mining',
#   'on',
#   'PoWhash',
#   '\x1b[96m#af9879dd\xe2\x80\xa6\x1b[0m',
#   ':',
#   '0',
#   'H/s',
#   '=',
#   '0',
#   'hashes',
#   '/',
#   '0.5',
#   's\n']

# hammer hexcode 01f528 Mined block block number [maybe not that order]


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
while True:
    line = process.stderr.readline()
    if line == '':
        break

    parts = line.split(' ')
    stripped = filter(lambda x: len(x) != 0, parts)

    if len(stripped) > 9:
        if stripped[9] == 'H/s':
            HPS = int(stripped[8])

    if (time.time() - timeCheck) > 5:
        print 'Current Hashes/Second: %s' % readableHash(HPS)
        timeCheck = time.time()

process.wait()