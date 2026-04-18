#!/usr/bin/python3
'''
insert shim code into webpage

proof of concept which may turn out to be production code
'''
try:
    from HTMLParser import HTMLParser
except ImportError:
    from html.parser import HTMLParser
import sys, logging  # pylint: disable=multiple-imports
logging.basicConfig(level=logging.DEBUG if __debug__ else logging.INFO)

class ShimmerParser(HTMLParser):
    '''
    parser that inserts a script tag with shim code
    '''
    shim = '<script src="/legaproxy/shims.js"></script>'

    def __init__(self, *args, **kwargs):
        super(ShimmerParser, self).__init__(*args, **kwargs)
        self.parts = []
        self.tags = []
        self.shimmed = False

    def handle_starttag(self, tag, attrs):
        '''
        handle start tag
        '''
        logging.debug('handling start tag %s', tag)
        self.tags.append(tag)
        before = after = ''
        if not self.shimmed:
            if tag == 'head':
                after = self.shim
                self.shimmed = True
            elif tag in ('body', 'div', 'p'):
                before = self.shim
                self.shimmed = True
        self.parts.append(before + '<' + tag + expand_attrs(attrs) +
                          '>' + after)

    def handle_endtag(self, tag):
        '''
        handle end tag
        '''
        logging.debug('handling end tag %s', tag)
        while self.tags[-1] != tag:
            popped = self.tags.pop(-1)
            logging.debug('popped unexpected tag %s', popped)
        self.tags.pop(-1)
        self.parts.append('</' + tag + '>')

    def handle_startendtag(self, tag, attrs):
        '''
        handle xml <tag/>
        '''
        logging.debug('handling start end tag %s', tag)
        self.parts.append('<' + tag + expand_attrs(attrs) + '/>')

    def handle_comment(self, data):
        '''
        handle html comment
        '''
        logging.debug('handling comment %s', data)
        self.parts.append('<!-- ' + data + '-->')

    def handle_charref(self, name):
        '''
        handle character reference
        '''
        logging.debug('handling charref %r', name)
        self.parts.append('&#' + name + ';')

    def handle_entityref(self, name):
        '''
        handle html entity
        '''
        logging.debug('handling entityref %r', name)
        self.parts.append('&' + name + ';')

    def handle_decl(self, decl):
        '''
        handle html declaration
        '''
        logging.debug('handling decl %r', decl)
        self.parts.append('<!' + decl + '>')

    def handle_data(self, data):
        '''
        handle data
        '''
        logging.debug('self: %s, data: %r', vars(self), data)
        self.parts.append(data)

    def handle_pi(self, data):
        '''
        handle processing instruction

        (I don't know what this is... guess I'll find out eventually--jc)
        '''
        logging.debug('self: %s, pi: %r', vars(self), data)
        self.parts.append(data)

def shim(filename=None):
    '''
    add shim code to file or stdin
    '''
    with open(filename, 'r', encoding='utf-8') \
            if filename not in [None, '-'] \
            else sys.stdin as infile:
        parser = ShimmerParser(convert_charrefs=False)
        for line in infile:
            parser.feed(line)
        logging.debug('final parser.tags: %s', parser.tags)
        parser.close()
        print(''.join(parser.parts))

def shimtext(text):
    '''
    shim already-read html text
    '''
    parser = ShimmerParser(convert_charrefs=False)
    parser.feed(text)
    parser.close()
    return ''.join(parser.parts)

def expand_attrs(attrs):
    '''
    expand tag attributes

    >>> expand_attrs({'class': 'bleah', 'id': 'blargh', 'spam': 'spam spam'})
    'class="bleah" id="blargh" spam="spam spam"'
    '''
    result = ''
    for key, value in attrs:
        result += ' ' + key
        if value is not None:
            result += '="' + value + '"'
    return result

if __name__ == '__main__':
    shim(*sys.argv[1:])
