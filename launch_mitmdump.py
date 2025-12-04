#!/usr/bin/python3
'''
monkeypatch blinker._saferef for mitmproxy < 8.1.1-4, then start it
'''
# anticipate mitmproxy < 8.1.1-4 error `from blinker import _saferef`
import sys, logging  # pylint: disable=multiple-imports
logging.basicConfig(level=logging.DEBUG if __debug__ else logging.INFO)
try:
    import blinker
except ImportError:
    blinker = type('', (), {})  # pylint: disable=invalid-name
try:
    from blinker import _saferef
except ImportError:
    from saferef_patch import saferef_patch
    logging.debug('sys.modules: %r', sys.modules)
    blinker._saferef = sys.modules['saferef_patch'] 
from mitmdump import *
if __name__ == '__main__':
    # copied, with modifications, from /usr/bin/mitmdump on Debian
    sys.argv[0] = 'mitmdump'
    sys.exit(
        load_entry_point(
            'mitmproxy==8.1.1',
            'console_scripts',
            'mitmdump'
        )()
    )
