#!/usr/bin/python3
'''
parser companion to jslex.py
'''
import os
from jsfix import fixup
from jslex import GROUP, logging

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

def jsparse(tokens):
    ordered = []
    order = dict.fromkeys(GROUP, 0)
    openers = tuple(GROUP.keys())
    closers = tuple(GROUP.values())
    order.update({v: k for k, v in GROUP.items()})
    logging.debug('order: %s', order)
    for token in tokens:
        if token in openers:
            ordered.append((token, order[token]))
            order[token] += 1
        elif token in closers:
            order[order[token]] -= 1
            ordered.append((token, order[order[token]]))
        else:
            ordered.append((token, None))
    #return ordered
    for index in range(len(ordered)):
        pair = ordered[index]
        if pair[0] in openers:
            closer = ordered.index((GROUP[pair[0]], pair[1]), index)
            span = ''.join(tokens[index:closer + 1])
            logging.debug('found group length %d: %r', len(span), span)

if __name__ == '__main__':
    if os.path.exists('tokens.txt'):
        from ast import literal_eval
        with open('tokens.txt', 'r', encoding='utf-8') as testfile:
            testdata = literal_eval(testfile.read())
    elif os.path.exists('pathological.js'):
        os.environ['FIXUP_RETURN_TOKENS_ONLY'] = '1'
        with open('pathological.js', 'r', encoding='utf-8') as testfile:
            testdata = fixup(testfile.read())
    print(jsparse(testdata))
