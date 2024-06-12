#!/usr/bin/python3
'''
fast lexer for javascript

sacrifice completeness for speed

see references JavaScriptLexer.g4 and
developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Lexical_grammar

NOTES:
    iff="if and only if"
    nullish="null or undefined"
'''
import sys, logging, re  # pylint: disable=multiple-imports
from string import ascii_letters, digits
from collections import OrderedDict
logging.basicConfig(level=logging.DEBUG if __debug__ else logging.INFO)
WHITESPACE = tuple('\t\v\f \xa0\ufeff')  # may need to add more
ENDLINE = tuple('\n\r\u2028\u2029')
ZEROWIDTH = tuple('\u200c\u200d')  # non-joiner and joiner
COMMENTS = OrderedDict([
    ('/*', '*/'),
    ('//', ENDLINE),
    ('#!', ENDLINE),  # only valid at start of script, but lexer needn't care
])
STRING = OrderedDict([
    ('"', '"'),
    ("'", "'"),
    ('`', '`'),
])
GROUP = OrderedDict([
    ('{', '}'),
    ('[', ']'),
    ('(', ')'),
])
OPERATOR = [
    '>>>=',  # right shift logical assign
    '>>=',   # right shift arithmetic assign
    '=>',    # arrow
    '<<=',   # left shift assign
    '??=',   # nullish coalescing assign
    '**=',   # power assign
    '===',   # identity equals
    '>>>',   # right shift logical
    '!==',   # identity not equals
    '...',   # ellipsis ("spread" or "rest" syntax, like Python splat (*))
    '|=',    # bit-or assign
    '^=',    # bit-xor assign
    '*=',    # multiply assign
    '/=',    # divide assign
    '%=',    # modulus assign
    '+=',    # plus assign
    '-=',    # minus assign
    '&=',    # bit-and assign
    '?.',    # optional chaining (access property if LH not nullish)
    '||',    # logical or
    '&&',    # logical and
    '??',    # nullish coalesce (LH becomes RH iff LH is nullish)
    '++',    # increment
    '--',    # decrement
    '>>',    # right shift arithmetic
    '<<',    # left shift
    '<=',    # less than assign
    '>=',    # greater than assign
    '==',    # equals
    '!=',    # not equals
    '**',    # power
    '?',     # question ("if" as part of ternary operator `a ? b : c`)
    '|',     # bit-or
    '^',     # bit-xor
    '&',     # bit-and
    '~',     # bit-not
    '%',     # modulus
    '#',     # hash (precedes private field identifier in class definition)
    '>',     # greater than
    '<',     # less than
    '*',     # multiply
    '/',     # divide
    '+',     # plus
    '-',     # minus
    '=',     # assign
    '.',     # dot (property accessor, `a.b`, also expressed `a["b"]`)
    '!',     # not
    ':',     # colon
    ',',     # comma
    ';',     # semicolon
]
ID_START = tuple(ascii_letters + '$_')
ID_CONTINUE = ID_START + tuple(digits) + ZEROWIDTH
ID = re.compile('[' + ''.join(ID_START) + '][' +
                ''.join(ID_CONTINUE) + ']*')
OPERATORS = '|'.join([op.replace('|', r'\|') for op in OPERATOR])
GROUPS = '|'.join(['|'.join([k, v]) for k, v in GROUP.items()])
SPLITTER = re.compile('(' + '|'.join([OPERATORS, GROUPS]) + ')')
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
    logging.debug('OPERATORS: %r', OPERATORS)
    tokens = []

if __name__ == '__main__':
    if len(sys.argv) > 1:
        for filename in sys.argv[1:]:
            with open(filename, 'r', encoding='utf-8') as infile:
                print(jslex(infile.read()))
    else:
        logging.warning('Assuming data on stdin, ^D or ^C if none')
        print(jslex(sys.stdin.read()))
