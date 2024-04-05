#!/usr/bin/python3
"""
Generic access to Perle RESTful API

Provides get/put/post methods and automatic authorization.
Look at the main() for sample code.
"""
import os
import time
import requests
import tempfile
import pickle

__all__ = ['PSL_RESTfulAPI']


class PSL_RESTfulAPI:
    '''
    Generic access to Perle RESTful API

    Provides get/put/post methods and automatic authorization.
    '''

    # Storage for the login cookie
    _COOKIEFILE = os.path.join(os.getenv('HOME', tempfile.gettempdir()),
                               '.pslcookie')

    def __init__(self, username, password, host, port=8080,
                 schema='http', ver='v1.1', retries=10, logcb=None):
        '''
        Initialize with given username/password at host.

        port: port to use
        schema: http or https
        ver: API version
        retries: how many connection retry attempts
        logcb: a log callback function which takes a single str.
        '''
        self.url_prefix = f'{schema}://{host}:{port}/api/{ver}/managed-devices'
        self.username = username
        self.password = password
        self.cookie = None
        self.retries = max(1, retries)
        if logcb is not None and not callable(logcb):
            raise TypeError('logcb must be callable')
        self.logcb = logcb
        self.loadcookie()
        if not self.cookie:
            self.login()

    def _requestop(self, op, args):
        '''Run a generic request operation, retrying login if required'''
        def badlogin(resp):
            return ((resp.status_code == 401) or
                    (b'Missing authorization' in resp.content) or
                    (b'User is not authorized' in resp.content))

        args['cookies'] = self.cookie

        # Try the request, retrying on any IO error (RESTful probably down)
        sleeptime = 1
        for retry in range(self.retries):
            conerr = None
            try:
                resp = op(**args)
                break
            except (ConnectionError, requests.RequestException) as e:
                if self.logcb is not None:
                    self.logcb(f'Connection failed - retrying '
                               f'({retry} of {self.retries}): {e}')
                conerr = e
                time.sleep(sleeptime)
                sleeptime = min(sleeptime*2, 16)

        if conerr is not None:
            # Give up
            raise conerr

        if badlogin(resp):
            # Redo login and try again
            self.login()
            args['cookies'] = self.cookie
            resp = op(**args)
            if badlogin(resp):
                raise Exception(resp.content)

        return resp

    def get(self, url, cmd={}):
        '''Perform a GET.  cmd unused here.'''
        api_url = self.url_prefix + url
        return self._requestop(requests.get, {'url': api_url})

    def put(self, url, cmd={}):
        '''Perform a PUT'''
        if not isinstance(cmd, dict):
            raise TypeError('dict-like object required for cmd')
        api_url = self.url_prefix + url
        return self._requestop(requests.put, {'url': api_url, 'json': cmd})

    def post(self, url, cmd={}):
        '''Perform a POST'''
        if not isinstance(cmd, dict):
            raise TypeError('dict-like object required for cmd')
        api_url = self.url_prefix + url
        return self._requestop(requests.post, {'url': api_url, 'json': cmd})

    def loadcookie(self):
        '''Load cached cookie'''
        try:
            with open(self._COOKIEFILE, 'rb') as fp:
                self.cookie = pickle.load(fp)
        except Exception:
            self.cookie = None

    def savecookie(self, cookie):
        '''Save current cookie in persistent storage'''
        if not cookie:
            return
        self.cookie = cookie
        with open(self._COOKIEFILE, 'wb') as fp:
            pickle.dump(self.cookie, fp)

    def login(self):
        '''Perform a login'''
        # Do not use self.post() to avoid login recursion.
        credentials = {'username': self.username, 'password': self.password}
        resp = requests.post(self.url_prefix + '/login', json=credentials)
        if not resp.ok:
            raise PermissionError('Invalid login')
        self.savecookie(resp.cookies.get_dict())


def main():
    '''Test mainline.  Adjust parameters for your location.'''
    USER = os.getenv('USER', 'admin')
    PASS = os.getenv('PASS', 'mypass')
    IP = os.getenv('IP', '192.168.0.123')
    print(f'Connecting as {USER}/{PASS} to host {IP}')
    irg = PSL_RESTfulAPI(USER, PASS, IP)

    data = irg.get('/system/general/clock').json()
    now = data['clock']
    print(f'api clock:  {now}')

    data = irg.put('/cli', {'show': 'show clock'}).json()
    now = data['cliCommands'][0]['commandOutput'].strip()
    print(f'show clock: {now}')

    data = irg.get('/network/cellular').json()
    print(f'cellular: {data["connectionInfo"]["cellularStatus"]}')


if __name__ == '__main__':
    main()
