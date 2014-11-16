#!/usr/bin/python

"""
Starts mysql containers on a set of volumes: /big/[b-z], wiping them out first,
and running mysql_install_db.

Usage: run.py <number-of-containers>
"""

import os, sys
from twisted.internet import reactor, defer, utils, task
from twisted.python import log

print 'disabling security'
os.system("setenforce 0")
# kill all containers
print 'killing containers...'
os.system("docker rm -f $(docker ps -a -q)")

concurrent = []
print 'starting up', sys.argv[1], 'of them...'
for i in range(ord('b'), ord('b') + int(sys.argv[1])):
    concurrent.append(i)
    x = chr(i)
    print 'doing', x
    path = "/big/%s" % (x,)
    hostPort = 4000 + i
    print 'allocating hostPort', hostPort
    os.system("rm -rf %s/*" % (path,))
    cmd = (("""docker run -v %s:/var/lib/mysql dockerfile/percona sh -c """
            """'mysql_install_db && mysqld_safe & mysqladmin --silent --wait=30 ping || exit 1 &&"""
            """ mysql -e "GRANT ALL PRIVILEGES ON *.* TO \\\"root\\\"@\\\"%%\\\" WITH GRANT OPTION;"'""") % (path,))
    print 'running', cmd
    os.system(cmd)
    os.system("docker run -d -v %s:/var/lib/mysql -v /root/block-perf-test/conf:/etc/mysql --publish=%d:3306 --name=mysql-%d-%s dockerfile/percona" % (path, hostPort, i, x))

"""
2. Load data
   * create database
     mysqladmin create tpcc1000
   * create tables
     mysql tpcc1000 < create_table.sql
   * create indexes and FK ( this step can be done after loading data)
     mysql tpcc1000 < add_fkey_idx.sql
   * populate data
     - simple step
       tpcc_load 127.0.0.1:33000 tpcc1000 root "" 1000
                 |hostname:port| |dbname| |user| |password| |WAREHOUSES|
       ref. tpcc_load --help for all options
     - load data in parallel
       check load.sh script

3. start benchmark
   * ./tpcc_start -h127.0.0.1 -P33000 -dtpcc1000 -uroot -w1000 -c32 -r10 -l10800
                  |hostname| |port| |dbname| |user| |WAREHOUSES| |CONNECTIONS| |WARMUP TIME| |BENCHMARK TIME|
   * ref. tpcc_start --help for all options
"""

def printIt(result):
    print result

WAREHOUSES = 2

def run(cmd, args, **kw):
    print "running", cmd, args
    return utils.getProcessOutput(cmd, args, errortoo=True)

def inject():
    dlist = []
    for i in concurrent:
        hostPort = 4000 + i
        # XXX This is getting bound too late.
        print 'creating database for', hostPort
        d = task.deferLater(reactor, 10, run, "mysqladmin",
            ("-h localhost -P %d --protocol=tcp --silent --wait=30 ping" % (hostPort,)).split(" "))
        d.addCallback(printIt)
        d.addCallback(lambda ignored: run("mysqladmin",
            ("-h localhost -P %d --protocol=tcp create tpcc1000" % (hostPort,)).split(" ")))
        d.addCallback(printIt)
        d.addCallback(lambda ignored: run("bash", ["-c",
            "mysql -h localhost -P %d --protocol=tcp tpcc1000 < /root/tpcc-mysql/create_table.sql" % (hostPort,)]))
        d.addCallback(printIt)
        d.addCallback(lambda ignored: run("bash", ["-c",
            "mysql -h localhost -P %d --protocol=tcp tpcc1000 < /root/tpcc-mysql/add_fkey_idx.sql" % (hostPort,)]))
        d.addCallback(printIt)
        d.addCallback(lambda ignored: run('/root/tpcc-mysql/tpcc_load',
            ["127.0.0.1:%d" % (hostPort,), "tpcc1000", "root", "", "%d" % (WAREHOUSES,)]))
        d.addCallback(printIt)
        d.addErrback(log.err, 'failed while creating database %d' % (i,))
        dlist.append(d)
    return defer.gatherResults(dlist)


def writeIt(result, hostPort):
    print result
    print "^ saving for", hostPort
    f = open("/root/results-twisted-%d.log" % (hostPort,), "w")
    f.write(result)
    f.close()

def benchmark():
    dlist = []
    for i in concurrent:
        hostPort = 4000 + i
        d = run("bash", ["-c",
            ('/root/tpcc-mysql/tpcc_start -h127.0.0.1 -P%d -dtpcc1000 -uroot -w%d -c32 -r10 -l120'
             ' > /root/results-%d.log')
            % (hostPort, WAREHOUSES, hostPort)])
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
