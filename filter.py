#!/usr/bin/python3
'''
Using example internet-in-mirror.py from
https://docs.mitmproxy.org/stable/addons-examples/
'''
import os, logging, base64, hashlib  # pylint: disable=multiple-imports
try:
    from mitmproxy import http
except (ImportError, ModuleNotFoundError):  # for doctests
    http = type('', (), {'HTTPFlow': None})  # pylint: disable=invalid-name

logging.basicConfig(level=logging.DEBUG if __debug__ else logging.WARNING)
HOSTSUFFIX = 'redwoodcu.org'
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
        logging.info('dropping spyware(?) junk from gvt1.com')
        flow.kill()
    logging.debug('request: %s', vars(flow.request))
    logging.info('flow.live: %s', flow.live)
    logging.info('request.method: %s', flow.request.method)
    for header, value in flow.request.headers.items():
        logging.info('header "%s": "%s"', header, value)

def response(flow: http.HTTPFlow) -> None:
    '''
    filter responses
    '''
    hostname = flow.request.host
    uahash = md5sum(flow.request.headers['user-agent'])
    if hostname.endswith(HOSTSUFFIX):
        savefile(
            os.path.join(
                FILES, hostname, uahash, *flow.request.path_components),
            flow.response.content
        )
        logging.info('flow.request.path: %s', flow.request.path)
    else:
        logging.info('Not filtering request for %s', flow.request.path)
    mimetype = flow.response.headers.get('content-type')
    if mimetype == 'text/html':
        logging.debug('processing any script tags in html')
    elif mimetype.endswith('/javascript'):
        logging.debug('processing %s file', mimetype)

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
    except OSError as failed:
        logging.error('could not write %s: %s', path, failed)
    except TypeError as failed:
        logging.error('could not write contents of %s: %s', path, failed)
        if retry_ok:
            savefile(path, contents, True, True, False)
            logging.info('wrote %s successfully as bytes', path)

# vim: set tabstop=4 expandtab shiftwidth=4 softtabstop=4
