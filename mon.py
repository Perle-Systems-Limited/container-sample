#!/usr/bin/python3
"""
Sample code using pslrestful to interact with a Perle router.
Can be run locally using a remote router or within a container in the router.
"""
import sys
import os
import time
import pslrestful


class Monitor(pslrestful.PSL_RESTfulAPI):
    '''Monitor router for hardware events'''

    def __init__(self, username, password, host, port):
        '''Initialize superclass with authentication info'''
        super().__init__(username, password, host, port)

    def getSysInfo(self):
        '''Get router system info'''
        sysinfo = self.get('/system').json()
        return sysinfo['sysInfo']

    def getIfs(self):
        '''Return dict of name to bytes (in, out) for all interfaces'''
        ret = {}
        ifs = self.get('/interfaces').json()
        for iface in ifs['interfaces']:
            name = iface['interfaceName']
            ib = iface['inBytes']
            ob = iface['outBytes']
            ret[name] = (int(ib), int(ob))
        return ret

    def getCell_Status_CID_TAC(self):
        '''Get cellular Status, CID and TAC (-1 if not available)'''
        cellinfo = self.get('/network/cellular').json()
        CID = TAC = -1
        netinfo = cellinfo.get('networkInfo', None)
        if netinfo:
            CID = netinfo.get('cellId', -1)
            TAC = netinfo.get('tac', -1)
        status = cellinfo["connectionInfo"]["cellularStatus"]
        return status, CID, TAC


def main(IP, PORT, USER, PASS):
    '''Monitor mainline'''

    # Optional delay override
    DELAY = int(os.getenv('DELAY', '5'))
    # Optional loops
    LOOPS = int(os.getenv('LOOPS', '10'))

    # Print stats every DELAY seconds.
    # You can use "show container log" to look at the container output.
    # You can use "container connect" to attach directly to the container.
    mon = Monitor(USER, PASS, IP, PORT)
    sysinfo = mon.getSysInfo()
    print('Router name:', sysinfo['systemName'])
    for _ in range(LOOPS):
        ifs = mon.getIfs()
        status, cid, tac = mon.getCell_Status_CID_TAC()

        print('===========', time.ctime())
        print(f'Cellular: stat={status} CID={cid} TAC={tac}')
        print('Interfaces I/O:')
        for key in ifs:
            i, o = ifs[key]
            print(f' {key:12}: {i:16} {o:16}')

        time.sleep(DELAY)
    return 0


def usage(name):
    usage = f'''Usage: {name} [IP PORT USER PASS]

IP PORT USER PASS can also be set in the environment.
On Unix:

    export IP=192.168.0.123
    export PORT=8080
    export USER=admin
    export PASS=mypasswd

On Windows:

    set IP=192.168.0.123
    set PORT=8080
    set USER=admin
    set PASS=mypasswd'''

    print(usage, file=sys.stderr)


if __name__ == '__main__':
    if len(sys.argv) == 5:
        # Args given
        sys.exit(main(*sys.argv[1:]))
    elif len(sys.argv) != 1:
        # Invalid args
        sys.exit(usage(sys.argv[0]))
    else:
        # Get args from environment
        IP = os.getenv('IP')
        PORT = os.getenv('PORT')
        USER = os.getenv('USER')
        PASS = os.getenv('PASS')
        if not all((IP, PORT, USER, PASS)):
            sys.exit(usage(sys.argv[0]))
        sys.exit(main(IP, PORT, USER, PASS))
