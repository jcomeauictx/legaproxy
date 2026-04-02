async def response(flow):  # pylint: disable=too-many-branches
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
    encoded = text.encode()
    if hostname.endswith(HOSTSUFFIX):
        logging.debug('response path: %s', flow.request.path_components)
        savefile(
            os.path.join(
                FILES, hostname, uahash, TIMESTAMP,
                *flow.request.path_components
            ),
            encoded, mimetype
        )
        logging.debug('flow.request.path: %s', flow.request.path)
    else:
        logging.debug('not saving %s', flow.request.path)
    if mimetype == 'text/html':
        logging.debug('adding shims and processing scripts in html')
        try:
            if 'asyncio' in sys.modules:
                exec('fixed = await asyncio.to_thread(shimtext, text)')
            else:
                fixed = shimtext(text)
        except (ValueError, IndexError) as problem:
            logging.error('call to shim failed: %s', problem)
        if fixed and fixed != text:
            logging.debug('shim modified html, saving to %s', MODIFIED)
            savefile(os.path.join(
                MODIFIED, hostname, uahash, TIMESTAMP,
                *flow.request.path_components
                ),
                fixed.encode(), mimetype, overwrite=True
            )
            flow.response.content = encode(fixed)
        else:
            logging.debug("shim didn't change content of html")
    elif mimetype.endswith('/javascript'):
        logging.debug('processing %s file', mimetype)
        if 'asyncio' in sys.modules:
            exec(
                'fixed = await asyncio.to_thread(fixup, text, flow.request.path)'
                )
        else:
            fixed = fixup(text, flow.request.path)
        if fixed != text:
            logging.debug('fixup modified script, saving to %s', MODIFIED)
            savefile(os.path.join(
                MODIFIED, hostname, uahash, TIMESTAMP,
                *flow.request.path_components
                ),
                fixed.encode(), mimetype, overwrite=True
            )
            flow.response.content = encode(fixed)
        else:
            logging.debug("fixup didn't change content of script")
    else:
        logging.debug('passing mime-type %s through unprocessed', mimetype)


