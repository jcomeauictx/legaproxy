#!/usr/bin/python3
'''
Using example internet-in-mirror.py from
https://docs.mitmproxy.org/stable/addons-examples/
'''
import os, logging, base64, hashlib  # pylint: disable=multiple-imports
from time import strftime
try:
    from mitmproxy import http
except (ImportError, ModuleNotFoundError):  # for doctests
    http = type('', (), {'HTTPFlow': None})  # pylint: disable=invalid-name

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
# iphone6 (iOS 12.5.7) user-agent string
USERAGENT = ('Mozilla/5.0 (iPhone; CPU iPhone OS 12_5_7 like Mac OS X) '
             'AppleWebKit/605.1.15 (KHTML, like Gecko) '
             'Version/12.1.2 Mobile/15E148'
)

def request(flow: http.HTTPFlow):
    '''
    filter requests
    '''
    if flow.request.host.endswith('gvt1.com'):
        logging.debug('dropping spyware(?) junk from gvt1.com')
        flow.kill()
    logging.debug('request: %s', vars(flow.request))
    logging.debug('flow.live: %s', flow.live)
    logging.debug('request.method: %s', flow.request.method)
    for header, value in flow.request.headers.items():
        logging.debug('header "%s": "%s"', header, value)

def response(flow: http.HTTPFlow) -> None:
    '''
    filter responses
    '''
    hostname = flow.request.host
    uahash = md5sum(flow.request.headers['user-agent'])
    if hostname.endswith(HOSTSUFFIX):
        logging.debug('response path: %s', flow.request.path_components)
        savefile(
            os.path.join(
                FILES, hostname, uahash, TIMESTAMP,
                *flow.request.path_components),
            flow.response.content
        )
        logging.debug('flow.request.path: %s', flow.request.path)
    else:
        logging.debug('Not filtering request for %s', flow.request.path)
    logging.debug('response headers: %s', flow.response.headers)
    for header, value in flow.response.headers.items():
        logging.debug('header "%s": "%s"', header, value)
    mimetype = flow.response.headers.get('content-type') or ''
    if mimetype == 'text/html':
        logging.debug('processing any script tags in html')
    elif mimetype.endswith('/javascript'):
        logging.debug('processing %s file', mimetype)
    else:
        logging.debug('passing mime-type %s through unprocessed', mimetype)

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

def savefile(path, contents, binary=False, overwrite=False, retry_ok=True):
    '''
    write contents to disk under given path
    '''
    mode = 'wb' if binary else 'w'
    if os.path.exists(path) and not overwrite:
        logging.warning('not overwriting %s', path)
        return
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # pylint: disable=unspecified-encoding
        with open(path, mode) as outfile:
            outfile.write(contents)
            logging.debug('wrote %s successfully as %s', path,
                          'binary' if binary else 'string')
    except OSError as failed:
        logging.error('could not write %s: %s', path, failed)
    except TypeError as failed:
        if retry_ok:
            savefile(path, contents, True, True, False)
        else:
            logging.error('could not write contents of %s: %s', path, failed)

# vim: set tabstop=4 expandtab shiftwidth=4 softtabstop=4
