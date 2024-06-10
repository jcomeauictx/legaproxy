#!/usr/bin/python3
'''
fast lexer for javascript

sacrifice completeness for speed
'''
import sys, logging, re  # pylint: disable=multiple-imports
from string import ascii_letters, digits
logging.basicConfig(level=logging.DEBUG if __debug__ else logging.INFO)
WHITESPACE = tuple('\t\v\f \xa0\ufeff')  # may need to add more
ENDLINE = tuple('\n\r\u2028\u2029')
COMMENTS = {
    '//': ENDLINE,
    '#!': ENDLINE,  # only valid at start of script, but lexer needn't care
    '/*': '*/',
}
STRING = {
    '"': '"',
    "'": "'",
    '`': '`',
}
GROUP = {
    '{': '}',
    '[': ']',
    '(': ')',
}
OPERATOR = [
    '>>>=',
    '>>=',
    '=>',
    '<<=',
    '??=',
]
ID_START = tuple(ascii_letters + '$_')
ID_CONTINUE = ID_START + tuple(digits)
ID = re.compile('[' + ''.join(ID_START) + '][' +
                ''.join(ID_CONTINUE) + ']*')
KEYWORDS = [
    'break',
    'case',
    'catch',
    'class',
    'const',
    'continue',
    'debugger',
    'default',
    'delete',
    'do',
    'else',
    'export',
    'extends',
    'false',
    'finally',
    'for',
    'function',
    'if',
    'import',
    'in',
    'instanceof',
    'new',
    'null',
    'return',
    'super',
    'switch',
    'this',
    'throw',
    'true',
    'try',
    'typeof',
    'var',
    'void',
    'while',
    'with',
]

def jslex(string):
    '''
    break input string into lexical elements

    //developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Lexical_grammar
    '''
    tokens = []
    

if __name__ == '__main__':
    if len(sys.argv) > 1:
        for filename in sys.argv[1:]:
            with open(filename, 'r', encoding='utf-8') as infile:
                print(jslex(infile.read()))
    else:
        logging.warning('Assuming data on stdin, ^D or ^C if none')
        print(jslex(sys.stdin.read()))
