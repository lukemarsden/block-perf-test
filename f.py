from twisted.internet import utils, reactor
from twisted.python import log

def printIt(result):
    print result

def foo():
    f = open('f', 'w')
    f.write('f')
    f.close()

    d = utils.getProcessOutput("bash", ["-c", "cat < f"])
    d.addErrback(log.err, 'oops')
    d.addCallback(printIt)
    d.addBoth(lambda ignored: reactor.stop())

reactor.callWhenRunning(foo)
reactor.run()
