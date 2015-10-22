#!/usr/bin/python

usage = """
Starts mysql containers on a set of volumes: /big/[b-z], wiping them out first,
and running mysql_install_db.

Usage: run.py <number-of-containers> <warehouses-per-benchmark> <test-time-in-seconds> <do-load-step:1=yes,0=no>

Set do-load-step to 0 if you have already created and loaded the databases.
"""

import os, sys
from twisted.internet import reactor, defer, utils, task
from twisted.python import log

if len(sys.argv) < 5:
    print usage
    raise SystemExit()

CONCURRENCY = int(sys.argv[1])
WAREHOUSES = int(sys.argv[2]) # 2
TEST_TIME = int(sys.argv[3]) # 120
DO_LOAD_STEP = int(sys.argv[4])

print 'disabling security'
os.system("setenforce 0")

concurrent = []
for i in range(ord('b'), ord('b') + CONCURRENCY):
    concurrent.append(i)

if DO_LOAD_STEP:
    # kill all containers
    print 'killing containers...'
    os.system("docker rm -f $(docker ps -a -q)")

    print 'starting up', CONCURRENCY, 'of them...'
    for i in concurrent:
        x = chr(i)
        print 'doing', x
        path = "/big/%s" % (x,)
        hostPort = 4000 + i
        print 'allocating hostPort', hostPort
        os.system("rm -rf %s/*" % (path,))
        cmd = (("""docker run -v %s:/var/lib/mysql percona sh -c """
                """'mysql_install_db && mysqld_safe & mysqladmin --silent --wait=30 ping || exit 1 &&"""
                """ mysql -e "GRANT ALL PRIVILEGES ON *.* TO \\\"root\\\"@\\\"%%\\\" WITH GRANT OPTION;"'""") % (path,))
        print 'running', cmd
        os.system(cmd)
        os.system("docker run -d -v %s:/var/lib/mysql -v /home/ec2-user/block-perf-test/conf:/etc/mysql --publish=%d:3306 --name=mysql-%d-%s percona" % (path, hostPort, i, x))

def printIt(result):
    print result

def run(cmd, args, **kw):
    print "running", cmd, args
    return utils.getProcessOutput(cmd, args, errortoo=True)

def inject():
    dlist = []
    for i in concurrent:
        hostPort = 4000 + i
        print 'creating database for', hostPort
        d = task.deferLater(reactor, 10, run, "mysqladmin",
            ("-h localhost -P %d --protocol=tcp --silent --wait=30 ping" % (hostPort,)).split(" "))
        d.addCallback(printIt)
        d.addCallback(lambda ignored, hp: run("mysqladmin",
            ("-h localhost -P %d --protocol=tcp create tpcc1000" % (hp,)).split(" ")), hp=hostPort)
        d.addCallback(printIt)
        d.addCallback(lambda ignored, hp: run("bash", ["-c",
            "mysql -h localhost -P %d --protocol=tcp tpcc1000 < /home/ec2-user/tpcc-mysql/create_table.sql" % (hp,)]), hp=hostPort)
        d.addCallback(printIt)
        d.addCallback(lambda ignored, hp: run("bash", ["-c",
            "mysql -h localhost -P %d --protocol=tcp tpcc1000 < /home/ec2-user/tpcc-mysql/add_fkey_idx.sql" % (hp,)]), hp=hostPort)
        d.addCallback(printIt)
        if DO_LOAD_STEP:
            d.addCallback(lambda ignored, hp: run('/home/ec2-user/tpcc-mysql/tpcc_load',
                ["127.0.0.1:%d" % (hp,), "tpcc1000", "root", "", "%d" % (WAREHOUSES,)]), hp=hostPort)
            d.addCallback(printIt)
        d.addErrback(log.err, 'failed while creating database %d' % (i,))
        dlist.append(d)
    return defer.gatherResults(dlist)

def writeIt(result, hostPort):
    print result
    print "^ saving for", hostPort
    f = open("/home/ec2-user/results-twisted-%d.log" % (hostPort,), "w")
    f.write(result)
    f.close()

def benchmark():
    dlist = []
    for i in concurrent:
        hostPort = 4000 + i
        d = run("bash", ["-c",
            ('/home/ec2-user/tpcc-mysql/tpcc_start -h127.0.0.1 -P%d -dtpcc1000 -uroot -w%d -c32 -r10 -l%d'
             ' > /home/ec2-user/results-%d-%d-%d-%d.log')
            % (hostPort, WAREHOUSES, TEST_TIME,
               CONCURRENCY, WAREHOUSES, TEST_TIME, hostPort)])
        d.addCallback(writeIt, hostPort=hostPort)
        dlist.append(d)
    return defer.gatherResults(dlist)

def main():
    d = inject()
    d.addCallback(printIt)
    d.addCallback(lambda ignored: benchmark())
    d.addCallback(printIt)
    d.addErrback(log.err, 'failed while running entire benchmark')
    d.addBoth(lambda ignored: reactor.stop())
    return d

reactor.callWhenRunning(main)
reactor.run()
