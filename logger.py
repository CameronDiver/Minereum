from datetime import datetime
from subprocess import call, Popen, PIPE
import sys

class Logger(object):
    def __init__(self):

        self.colours = {
            'blue'     : '\033[94m',
            'darkred'  : '\033[93m',
            'red'      : '\033[93m',
            'lightred' : '\033[91m',
            'cyan'     : '\033[36m',
            'purple'   : '\033[35m',
            'green'    : '\033[32m',
            'yellow'   : '\033[33m',

            'bold-purple' : '\033[1;94m',
            'bold-red'    : '\033[1;93m',
            'bold-green'   : '\033[1;92m',
            'bold-white'  : '\033[1;97m',
            'bold-cyan'   : '\033[1;92m',
            'bold-pink'   : '\033[1;95m',
            'bold-blue'  : '\033[1;96m',

            'bg-yellow': '\033[43m',
            'bg-gray'  : '\033[47m', 
            'bg-red'   : '\033[41m',
            'bg-green' : '\033[42m',
            'bg-pink'  : '\033[45m',

            'bold'     : '\033[1m',
            'end'      : '\033[0m'
        }


        self.sourceColours = {
            'ERROR': 'bg-red',
            'ethminer': 'bold-blue',
            'geth': 'bold-red',
            'time': 'bg-green',
            'info': 'bold-green'
        }

        self.dynamicLine = False
        self.dynamic = ('', '', '')

        self.offsetSize = self.getMaxSourceLength()

        self.offsetWithoutSource = len(datetime.now().strftime('%H:%M')) + 1

        self.offset = self.offsetWithoutSource + self.offsetSize

        self.termLineLength = self.getTermLineLength()

    def getMaxSourceLength(self):
        a = [len(source) for source in self.sourceColours]
        return max(a)

    def getTermLineLength(self):
        p = Popen(['tput', 'cols'], stdout=PIPE)
        output = p.communicate()
        p.wait()

        return int(output[0].strip())


    def addSrcColour(self, source, colourName):
        assert colourName in self.colours
        self.sourceColours[source] = colourName

    def log(self, source, message):
        if self.dynamicLine is False:
            self.internalLog(source, message)
        else:
            self.clearLine()
            self.internalLog(source, message)
            self.internalLogDyn(self.dynamic[1], self.dynamic[2])


    def clearLine(self):
        # clear the current line
        print '\r'+' '*(self.termLineLength-1)+'\r',
        
    def internalLog(self, source, message):
        print '[%s%s%s %s %s%s] %s' % (
            self.colours[self.sourceColours['time']],
            datetime.now().strftime('%H:%M'),
            self.colours['end'],
            self.colours[self.sourceColours[source]],
            source,
            self.colours['end'],
            message)
        
    def internalLogDyn(self, source, message):
        print '[%s%s%s %s %s%s] %s' % (
            self.colours[self.sourceColours['time']],
            datetime.now().strftime('%H:%M'),
            self.colours['end'],
            self.colours[self.sourceColours[source]],
            source,
            self.colours['end'],
            message),
        sys.stdout.flush()
        
    def logDynamic(self, source, dynId, message):
        if self.dynamicLine:
            if dynId == self.dynamic[0]:
                
                # standard case, dynamic line updating itself
                self.clearLine()
                self.internalLogDyn(source, message)
                self.dynamic = (dynId, source, message)
            else:
                if dynId[0] != '/':
                    # Start of a new dynamic line
                    # save the current one by printing a newline
                    if message != '':
                        self.dynamic = (dynId, source, message)
                        print ''
                        self.internalLogDyn(source, message)
                else:
                    # the end of a dynamic line
                    if dynId[1:] == self.dynamic[0]:
                        self.dynamicLine = False
                        self.dynamic = ('', '', '')
                        self.clearLine()
                        self.internalLog(source, message)
                    else:
                        # another end coming when there is a new one opem
                        # just display it normally
                        self.clearLine()
                        self.internalLog(source, message)
                        self.internalLogDyn(self.dynamic[1], self.dynamic[2])
        else:
            self.internalLogDyn(source, message)
            self.dynamic = (dynId, source, message)
            self.dynamicLine = True
    
    def logColour(self, source, text, colour):
        self.log(source, self.integrateColour(text, colour))

    def logColours(self, source, texts, colours):
        out = ''
        for text, col in zip(texts, colours):
            out += self.integrateColour(text, col)
        self.log(source, out)

    def integrateColour(self, text, colour):
        return '%s%s%s' % (
                self.colours[colour],
                text,
                self.colours['end']
            )
