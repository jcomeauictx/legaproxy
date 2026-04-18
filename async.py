#!/usr/bin/python3
'''
mitmdump filter to test delayed responses
'''
import os, logging, time, asyncio  # pylint: disable=multiple-imports
from http import HTTPStatus
from posixpath import split, sep
# the following are only for mitmproxy 0.9.x
from libmproxy.flow import Response
from libmproxy import controller

MIMETYPES = {
    '.html': 'text/html',
    '.png': 'image/png'
}

logging.basicConfig(level=logging.DEBUG if __debug__ else logging.INFO)

def request(flow):
    '''
    capture and modify Request object

    flow.request.path contains any querystring that may have been appended
    flow.request.path_components does not, but it can be a empty tuple,
    a singleton, or of indefinite length.
    '''
    logging.info('request received: %s, components: %s',
                 flow.request.url, flow.request.path_components)
    path = sep.join(flow.request.path_components)
    directory, filename = split(path)
    logging.info('path: %s, split: %s, exists: %s',
                 path, (directory, filename), os.path.exists(path))
    if flow.request.host.endswith('gvt1.com'):
        logging.info('dropping google spyware')
        flow.kill()
    elif flow.request.host in ('mitm', 'mitm.it'):
        logging.info('passing on request to mitm.it')
    elif directory == '' and filename in ('', 'index.html', 'favicon.ico'):
        logging.info('passing request on to server')
    elif directory == 'legaproxy' and os.path.exists(path):
        logging.info('serving file %s', path)
        mimetype = MIMETYPES.get(os.path.splitext(filename)[1], 'text/plain')
        response = Response(
            [1, 1],
            HTTPStatus.OK, "OK",
            ODictCaseless([['Content-Type', mimetype]]),
            read(path),
            None
        )
        flow.request.reply(response)
    elif directory == 'legaproxy' and filename == 'shutdown':
        logging.warning('shutting down MITM')
        response = Response(
            [1, 1],
            HTTPStatus.OK, "OK",
            ODictCaseless([['Content-Type', 'text/plain']]),
            b'shutting down MITM',
            None
        )
        controller.should_exit = True
    else:
        logging.warning('dropping unexpected request %s', flow.request.url)
        flow.kill()

async def response(flow):
    '''
    capture and modify Response object
    '''
    logging.info('response received: %s', flow.request.url)
    directory, filename = split(sep.join(flow.request.path_components))
    logging.debug('received request for directory %s, filename %s',
                  directory, filename)
    if directory == 'legaproxy' and filename.endswith('.png'):
        delay = int(flow.request.query.get('delay', '0').rstrip('s'))
        await asyncio.to_thread(swc, delay)
    elif directory == '' and filename in ('', 'index.html'):
        logging.info('filter: %s', __file__)
        filepath = os.path.join('legaproxy', __file__.replace('.py', '.html'))
        flow.response.content = read(filepath)

def swc(delay):
    '''
    simulate swc processing of javascript by delaying a fixed amount of time
    '''
    logging.info('delaying response by %d seconds', delay)
    time.sleep(delay)
    logging.info('done delaying response by %d seconds', delay)

def read(filename):
    '''
    read and return file contents as bytes
    '''
    with open(filename, 'rb') as infile:
        return infile.read()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
