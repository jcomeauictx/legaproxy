#!/usr/bin/python3
'''
legaproxy -- JavaScript translator for legacy devices

Based on example internet-in-mirror.py from
https://docs.mitmproxy.org/stable/addons-examples/

This might allow old computers/operating systems, smartphones, tablets,
iPod Touch, and many other legacy devices to access the modern Web.
'''
import sys, os, logging, base64, hashlib  # pylint: disable=multiple-imports
import posixpath as wwwpath
from time import strftime
from hashlib import sha256
from subprocess import Popen, PIPE
try:
    from mitmproxy import http
except ImportError:  # for doctests
    http = type('', (), {'HTTPFlow': None})  # pylint: disable=invalid-name
try:
    from libmproxy.flow import Response as LibmproxyResponse, ODictCaseless
except ImportError:
    LibmproxyResponse = None
    ODictCaseless = None
try:
    sys.path.append(os.getcwd())
    from shimmer import shimtext
except ImportError as problem:
    logging.error('cannot load shimmer from %s: %s', os.listdir('.'), problem)
    raise problem

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

def _respond(flow, code, body, content_type):
    '''
    short-circuit a flow with a synthetic response

    compatible with old libmproxy and new mitmproxy
    '''
    if LibmproxyResponse is not None:
        _response = LibmproxyResponse(
            flow.request, flow.request.httpversion,
            code, 'OK' if code == 200 else 'Not Found',
            ODictCaseless([['Content-Type', content_type]]),
            body, None
        )
        flow.request.reply(_response)
    else:
        flow.response = http.Response.make(
            code, body, {'Content-Type': content_type}
        )

def request(*args):
    '''
    filter requests

    old libmproxy: request(context, flow)
    new mitmproxy: request(flow)
    '''
    flow = args[-1]
    logging.debug('filter.request started')
    mimetypes = {
        '.png': 'image/png',
        '.html': 'text/html',
        '.js': 'application/javascript'
    }
    if flow.request.path.startswith('/legaproxy') and (
            flow.request.path == '/legaproxy' or
            flow.request.path[len('/legaproxy')] == '/'):
        logging.debug('MITM intercepting request for %s', flow.request.path)
        path = flow.request.path.lstrip('/')
        extension = wwwpath.splitext(path)[-1]
        if os.path.isfile(path):
            logging.debug('MITM returning local file %s', path)
            with open(path, 'rb') as infile:
                _respond(
                    flow, 200, infile.read(),
                    mimetypes.get(extension, 'application/octet-stream')
                )
        else:
            logging.debug('MITM could not find local file %s', path)
            _respond(flow, 404, b'404 File not found', 'text/html')
    elif flow.request.host.endswith('gvt1.com'):
        logging.debug('dropping spyware(?) junk from gvt1.com')
        flow.kill()
    else:
        logging.debug('request: %s', vars(flow.request))
        logging.debug('flow.live: %s', flow.live)
        logging.debug('request.method: %s', flow.request.method)
        for header, value in flow.request.headers.items():
            logging.debug('header "%s": "%s"', header, value)

def response(*args):
    '''
    filter responses

    old libmproxy: response(context, flow); new mitmproxy: response(flow)
    '''
    flow = args[-1]
    logging.debug('filter.response started')
    try:
        _response(flow)
    except Exception as exc:  # pylint: disable=broad-except
        logging.exception(
            'response hook failed: %s: %s', type(exc).__name__, exc
        )

def _path_components(flow):
    '''
    return path segments as a tuple, compatible with old and new mitmproxy

    avoids flow.request.path_components; old libmproxy's version
    caused infinite recursion.
    '''
    return tuple(p for p in flow.request.path.split('?')[0].split('/') if p)

def _header(value, default=''):
    '''
    normalize a header value: old libmproxy returns lists,
    new mitmproxy returns strings
    '''
    if isinstance(value, list):
        return value[0] if value else default
    return value if value is not None else default

def _response(flow):  # pylint: disable=too-many-branches, too-many-statements
    '''
    inner body of response hook, wrapped so old mitmproxy can't
    swallow exceptions silently
    '''
    hostname = flow.request.host
    ua = _header(flow.request.headers.get('user-agent') or
                 flow.request.headers.get('User-Agent'))
    uahash = md5sum(ua)
    logging.debug('response headers: %s', flow.response.headers)
    for header, value in flow.response.headers.items():
        logging.debug('header "%s": "%s"', header, value)
    mimetype = _header(
        flow.response.headers.get('content-type', '')
    ).split(';')[0]
    encode = str  # for encoding after modification
    try:
        text = flow.response.content.decode('utf-8')
        logging.debug('webpage text was utf-8 encoded')
        encode = lambda s: s.encode('utf-8')
    except UnicodeError:
        text = flow.response.content.decode('latin1')
        logging.debug('assuming webpage text latin1-encoded')
        # this can happen on binary/image data as well, but will be unused
        # pylint: disable=unnecessary-lambda-assignment
        encode = lambda s: s.encode('latin1')
    except AttributeError:
        text = flow.response.content
        logging.debug('webpage text was already decoded')
    encoded = text.encode('utf-8')
    if hostname.endswith(HOSTSUFFIX):
        logging.debug('response path: %s', _path_components(flow))
        savefile(
            os.path.join(
                FILES, hostname, uahash, TIMESTAMP,
                *_path_components(flow)
            ),
            encoded, mimetype
        )
        logging.debug('flow.request.path: %s', flow.request.path)
    else:
        logging.debug('not saving %s', flow.request.path)
    if mimetype == 'text/html':
        logging.debug('adding shims and processing scripts in html')
        fixed = None
        try:
            fixed = shimtext(text)
        except (ValueError, IndexError) as problem:
            logging.error('call to shim failed: %s', problem)
        if fixed and fixed != text:
            logging.debug('shim modified html, saving to %s', MODIFIED)
            savefile(os.path.join(
                MODIFIED, hostname, uahash, TIMESTAMP,
                *_path_components(flow)
                ),
                fixed.encode('utf-8'), mimetype, overwrite=True
            )
            flow.response.content = encode(fixed)
        else:
            logging.debug("shim didn't change content of html")
    elif mimetype.endswith('/javascript'):
        logging.debug('processing %s file', mimetype)
        fixed = fixup(text, flow.request.path)
        if fixed != text:
            logging.debug('fixup modified script, saving to %s', MODIFIED)
            savefile(os.path.join(
                MODIFIED, hostname, uahash, TIMESTAMP,
                *_path_components(flow)
                ),
                fixed.encode('utf-8'), mimetype, overwrite=True
            )
            flow.response.content = encode(fixed)
        else:
            logging.debug("fixup didn't change content of script")
    else:
        logging.debug('passing mime-type %s through unprocessed', mimetype)

def fixup(text, path):
    '''
    convert modern javascript to legacy code
    '''
    logging.info('starting conversion of %s to es3', path)
    command = Popen([
            'swc', 'compile',
            '--config-file', 'es3.swcrc',
            '--filename', path],
            stdin=PIPE, stdout=PIPE, stderr=PIPE)
    stdout, stderr = command.communicate(text.encode('utf-8'))
    logging.info('ending conversion of %s to es3', path)
    # chop echoed filename which is always sent
    stderr = ' '.join(stderr.decode('utf-8').split('\n')[1:]).rstrip()
    if stderr:
        logging.error('"swc convert" %s to ES3 problems: "%s"', path, stderr)
    if stdout:
        return stdout.decode('utf-8')
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
                return None
            # no `else` here, we will continue to overwrite
            logging.debug('savefile: overwriting %s', path)
        else:  # directory, so write as index file
            return savefile(
                os.path.join(path, 'index.html'),
                contents, mimetype, binary, overwrite, retry_ok
            )
    try:
        dirpath = os.path.dirname(path)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        # pylint: disable=unspecified-encoding
        with open(path, mode) as outfile:
            outfile.write(contents)
            logging.debug('savefile: wrote %s successfully as %s', path,
                          'binary' if binary else 'string')
    except OSError as failed:
        logging.error('could not write %s (%s): %s', path, mimetype, failed)
        if rebuild(os.path.dirname(path)):
            return savefile(
                path, contents, mimetype, binary, overwrite, retry_ok
            )
    except TypeError as failed:
        if retry_ok:
            return savefile(path, contents, mimetype, True, True, False)
        logging.error('could not write contents of %s (%s): %s',
                      path, mimetype, failed)
    return None

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
            newpath = os.path.join(path, 'index.html')
            with open(newpath, 'wb') as outfile:
                outfile.write(contents)
                logging.debug('rebuild: wrote %s successfully as %s',
                              newpath, 'binary')
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
