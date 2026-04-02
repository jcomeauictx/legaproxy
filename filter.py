#!/usr/bin/python3
'''
legaproxy -- JavaScript translator for legacy devices

Based on example internet-in-mirror.py from
https://docs.mitmproxy.org/stable/addons-examples/

This will allow old computers/operating systems, smartphones, tablets,
iPod Touch, and many other legacy devices to access the modern Web.
'''
import sys, os, logging, base64, hashlib  # pylint: disable=multiple-imports
from time import strftime
from hashlib import sha256
from subprocess import Popen, PIPE
try:
    from mitmproxy import http
except ImportError:  # for doctests
    http = type('', (), {'HTTPFlow': None})  # pylint: disable=invalid-name
try:
    sys.path.append(os.getcwd())
    from shimmer import shimtext
except ImportError as problem:
    logging.error('cannot load shimmer from %s: %s', os.listdir('.'), problem)
    raise problem
try:
    import asyncio
    with open('response.py') as codefile:
        exec(codefile.read())
except ImportError:  # python2
    with open('response.py') as codefile:
        code = codefile.read()
        if code.startswith('async '):
            code = code[len('async '):]
            logging.warning('python2: removed async from code: %s', code[:code.index('\n')])
        exec(code)

# set up our own logger separate from mitmproxy's, with level information
logger = logging.getLogger('legaproxy')
logger.addHandler(logging.StreamHandler())
logger.handlers[0].setFormatter(logging.Formatter(
    '[%(asctime)s.%(msecs)03d] legaproxy:%(levelname)s:%(message)s', '%H:%M:%S'))
logger.setLevel('DEBUG')
logging = logger
logging.debug('setting up filter')
# set HOSTSUFFIX= to save everything from all hosts
TIMESTAMP = strftime('%Y-%m-%dT%H%M%S')
HOSTSUFFIX = os.getenv('HOSTSUFFIX') or ''
FILES = os.path.join('storage', 'files')
MODIFIED = os.path.join('storage', 'modified')
# iphone6 (iOS 12.5.7) user-agent string
USERAGENT = ('Mozilla/5.0 (iPhone; CPU iPhone OS 12_5_7 like Mac OS X) '
             'AppleWebKit/605.1.15 (KHTML, like Gecko) '
             'Version/12.1.2 Mobile/15E148'
)

def request(flow):
    '''
    filter requests
    '''
    path = None
    if flow.request.path.startswith('/mitm/'):
        logging.debug('MITM intercepting request for %s', flow.request.path)
        path = flow.request.path.lstrip('/')
        if os.path.isfile(path):
            logging.debug('MITM returning local file %s', path)
            with open(path, 'rb') as infile:
                flow.response = http.Response.make(
                    200,
                    infile.read(),
                    {'Content-Type': 'application/javascript'}  # FIXME
                )
        else:
            logging.debug('MITM could not find local file %s', path)
            flow.response = http.Response.make(
                404,
                b'404 File not found',
                {'Content-Type': 'text/html'}
            )
    elif flow.request.host.endswith('gvt1.com'):
        logging.debug('dropping spyware(?) junk from gvt1.com')
        flow.kill()
    logging.debug('request: %s', vars(flow.request))
    logging.debug('flow.live: %s', flow.live)
    logging.debug('request.method: %s', flow.request.method)
    for header, value in flow.request.headers.items():
        logging.debug('header "%s": "%s"', header, value)

def fixup(text, path):
    '''
    convert modern javascript to legacy code
    '''
    logging.info('starting conversion of %s to es3', path)
    with Popen([
            'swc', 'compile',
            '--config-file', 'es3.swcrc',
            '--filename', path],
            stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True,
            encoding='utf-8') as command:
        stdout, stderr = command.communicate(text)
        logging.info('ending conversion of %s to es3', path)
        # chop echoed filename which is always sent
        stderr = ' '.join(stderr.split('\n')[1:]).rstrip()
    if stderr:
        logging.error('"swc convert" %s to ES3 problems: "%s"', path, stderr)
    if stdout:
        return stdout
    logging.error('swc could not convert %s, returning original', path)
    return text

def md5sum(string, base64encode=True):
    '''
    returns md5 hash of (byte)string, urlsafe_b64encoded by default

    >>> md5sum('test')
    'CY9rzUYh03PK3k6DJie09g=='
    >>> md5sum('test', False)
    '098f6bcd4621d373cade4e832627b4f6'
    '''
    try:
        hashed = hashlib.md5(string)
    except TypeError:
        hashed = hashlib.md5(string.encode())
    if base64encode:
        digest = base64.urlsafe_b64encode(hashed.digest()).decode()
    else:
        digest = hashed.hexdigest()
    return digest

def savefile( # pylint: disable=too-many-arguments,too-many-positional-arguments
        path, contents, mimetype=None, binary=False,
        overwrite=False, retry_ok=True
    ):
    '''
    write contents to disk under given path
    '''
    mode = 'wb' if binary else 'w'
    if os.path.exists(path):
        if os.path.isfile(path):
            if not overwrite:
                logging.warning('not overwriting %s', path)
                return
            # no `else` here, we will continue to overwrite
        else:  # directory, so write as index file
            path = os.path.join(path, 'index.html')
            savefile(path, contents, mimetype, binary, overwrite, retry_ok)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # pylint: disable=unspecified-encoding
        with open(path, mode) as outfile:
            outfile.write(contents)
            logging.debug('wrote %s successfully as %s', path,
                          'binary' if binary else 'string')
    except OSError as failed:
        logging.error('could not write %s (%s): %s', path, mimetype, failed)
        if rebuild(os.path.dirname(path)):
            savefile(path, contents, mimetype, binary, overwrite, retry_ok)
    except TypeError as failed:
        if retry_ok:
            savefile(path, contents, mimetype, True, True, False)
        else:
            logging.error('could not write contents of %s (%s): %s',
                          path, mimetype, failed)

def rebuild(path):
    '''
    Fix where a directory was saved as a file by moving contents to index.html

    Implemented recursively for code simplicity.

    >>> import tempfile
    >>> tempdir = tempfile.mkdtemp()
    >>> temppath = os.path.join(tempdir, 'a')
    >>> with open(temppath, 'ab') as temp:
    ...     logging.debug('touched %s', temppath)
    >>> rebuild(temppath)
    True
    >>> os.path.isfile(os.path.join(temppath, 'index.html'))
    True
    >>> os.remove(os.path.join(temppath, 'index.html'))
    >>> os.rmdir(temppath)
    >>> os.rmdir(tempdir)
    '''
    contents = None
    if path:
        if os.path.exists(path):
            if os.path.isdir(path):
                return True
            # presumed to be a file, we don't do symlinks
            logging.debug('rebuilding path %s', path)
            with open(path, 'rb') as infile:
                contents = infile.read()
            os.remove(path)
            os.makedirs(path)
            with open(os.path.join(path, 'index.html'), 'wb') as outfile:
                outfile.write(contents)
            return True
        # path doesn't exist, so try one level up
        return rebuild(os.path.dirname(path))
    # no path remaining, nothing to do
    return False

def sha256sum(bytestring):
    '''
    return sha256 digest as a hexadecimal string
    '''
    digest = None
    try:
        digest = sha256(bytestring).hexdigest()
    except TypeError:
        digest = sha256(bytestring.encode()).hexdigest()
    return digest
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
