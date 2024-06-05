#!/usr/bin/python3
'''
legaproxy -- JavaScript translator for legacy devices

Based on example internet-in-mirror.py from
https://docs.mitmproxy.org/stable/addons-examples/

This will allow old computers/operating systems, smartphones, tablets,
iPod Touch, and many other legacy devices to access the modern Web.
'''
import os, logging, base64, hashlib  # pylint: disable=multiple-imports
from time import strftime
from hashlib import sha256
from jsfix import fixup
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
MODIFIED = os.path.join('storage', 'modified')
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
    logging.debug('response headers: %s', flow.response.headers)
    for header, value in flow.response.headers.items():
        logging.debug('header "%s": "%s"', header, value)
    mimetype = flow.response.headers.get('content-type', '').split(';')[0]
    encode = str  # for encoding after modification
    try:
        text = flow.response.content.decode('utf-8')
        logging.debug('webpage text was utf-8 encoded')
        encode = str.encode
    except UnicodeError:
        text = flow.response.content.decode('latin1')
        logging.debug('assuming webpage text latin1-encoded')
        # this can happen on binary/image data as well, but will be unused
        # pylint: disable=unnecessary-lambda-assignment
        encode = lambda s: s.encode('latin1')
    except AttributeError:
        text = flow.response.content
        logging.debug('webpage text was already decoded')
    if hostname.endswith(HOSTSUFFIX):
        logging.debug('response path: %s', flow.request.path_components)
        savefile(
            os.path.join(
                FILES, hostname, uahash, TIMESTAMP,
                *flow.request.path_components
            ),
            flow.response.content, mimetype
        )
        logging.debug('flow.request.path: %s', flow.request.path)
    else:
        logging.debug('not saving %s', flow.request.path)
    if mimetype == 'text/html':
        logging.debug('processing any script tags in html')
    elif mimetype.endswith('/javascript'):
        logging.debug('processing %s file', mimetype)
        fixed = fixup(text)
        if fixed != text:
            logging.debug('fixup modified webpage, saving to %s', MODIFIED)
            savefile(os.path.join(
                MODIFIED, hostname, uahash, TIMESTAMP,
                *flow.request.path_components
                ),
                fixed, mimetype
            )
            flow.response.content = encode(fixed)
        else:
            logging.debug("fixup didn't change content of webpage")
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

def savefile(path, contents,  # pylint: disable=too-many-arguments
             mimetype=None, binary=False, overwrite=False, retry_ok=True):
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
# vim: set tabstop=4 expandtab shiftwidth=4 softtabstop=4
