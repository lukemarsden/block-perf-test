from twisted.internet import utils, reactor
from twisted.python import log

def printIt(result):
    print result

def foo():
    d = utils.getProcessOutput("bash", ["-c",
        "mysql -h localhost -P %d --protocol=tcp tpcc1000 < /root/tpcc-mysql/create_table.sql" % (1,)], errortoo=True)
    d.addErrback(log.err, 'oops')
    d.addCallback(printIt)
    d.addBoth(lambda ignored: reactor.stop())

reactor.callWhenRunning(foo)
reactor.run()
