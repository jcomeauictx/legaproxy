#!/usr/bin/python3
'''
parser companion to jslex.py
'''
import os
from jsfix import fixup
from jslex import GROUP, logging

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
    return ordered

if __name__ == '__main__':
    os.environ['FIXUP_RETURN_TOKENS_ONLY'] = '1'
    with open('pathological.js', 'r', encoding='utf-8') as testfile:
        testdata = fixup(testfile.read())
    print(jsparse(testdata))
