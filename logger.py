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
            'ERROR': 'bg-red'
        }

        self.gotDynamic = False
        self.currentDynamic = ('', '', '')

        self.dynamics = []

        self.termSize = self.getTermSize()

        # # Dont leave this here but use like this
        # self.nameColours = {
        #     'ethminer' : 'bold-blue',#'bg-green',
        #     'geth'     : 'bold-red',#'bg-red'

        #     'time'     : 'bg-green'
        # }
    
    def getTermSize(self):
        p = Popen(['tput', 'lines'], stdout=PIPE)
        output = p.communicate()
        p.wait()
        
        lines = int(output[0].strip())

        p = Popen(['tput', 'cols'], stdout=PIPE)
        output = p.communicate()
        p.wait()
        
        cols = int(output[0].strip())

        return (lines, cols)

    def addSrcColour(self, source, colourName):
        assert colourName in self.colours
        self.sourceColours[source] = colourName

    def log(self, source, message):
        # TODO: correct offset, not \t
        
        if self.gotDynamic:
            # clear the line to get rid of the dynamic part
            self.clearLine()

            # print the message
            self.internalLog(source, message)
            
            #print ' '
            # print the dynamic again
            self.internalLogDyn(self.currentDynamic[0], self.currentDynamic[2])
        else:
            self.internalLog(source, message)
        

    def clearLine(self):
        call(['tput', 'el1'])
        # call(['tput', 'cuu1'])
        self.moveCursorBack(self.getLastDynamicLength())

    def getLastDynamicLength(self):
        old = '[%s%s%s %s %s%s]\t%s' % (
                self.colours[self.sourceColours['time']],
                datetime.now().strftime('%H:%M'),
                self.colours['end'],
                self.colours[self.sourceColours[self.currentDynamic[0]]],
                self.currentDynamic[0],
                self.colours['end'],
                self.currentDynamic[2]
            )
        return len(old)

    def moveCursorBack(self, n):
        call(['tput', 'cub', str(n)])

    def savePlace(self):
        pass
        #call(['tput', 'sc'])

    def restorePlace(self):
        pass
        #call(['tput', 'rc'])

    def internalLog(self, source, message):
        print '[%s%s%s %s %s%s]\t%s' % (
                self.colours[self.sourceColours['time']],
                datetime.now().strftime('%H:%M'),
                self.colours['end'],
                self.colours[self.sourceColours[source]],
                source,
                self.colours['end'],
                message
            )
    def internalLogDyn(self, source, message):

        sys.stdout.write('[%s%s%s %s %s%s]\t%s' % (
                self.colours[self.sourceColours['time']],
                datetime.now().strftime('%H:%M'),
                self.colours['end'],
                self.colours[self.sourceColours[source]],
                source,
                self.colours['end'],
                message
            ))
        sys.stdout.flush()

    def logDynamic(self, source, dynId, message):

        # if(dynId[0] == '/'):
        #     for idx, dyn in self.dynamics:
        #         if dynId[1:] == dyn[1]:
        #             del self.dynamics[idx]
        #             break

        if self.gotDynamic:
            # check if its ending dynamic
            if dynId[0] == '/':
                if dynId[1:] == self.currentDynamic[1]:
                    self.gotDynamic = False

                self.clearLine()
                if message == '':
                    return
                self.internalLog(source, message)
                return

            
            if not self.currentDynamic[1] == dynId:
                # Commenting out this part and testing another, seeing if rather than
                # it being rigid and need dynamic outputs to be ended, it just switches to the other
                # didnt work, TODO: try this properly
                self.log('ERROR', "Internal error: DynamicOutput code error. Current: %s, given: %s" % (self.currentDynamic[1], dynId))
                sys.exit()
                # print a newline
                print ' '

            # clear the line
            self.clearLine()
            
            self.currentDynamic = (source, dynId, message)

            self.internalLogDyn(source, message)
        else:
            self.gotDynamic = True
            self.currentDynamic = (source, dynId, message)
            self.internalLogDyn(source, message)

    def stopDynamic(self):
        self.gotDynamic = False
            
