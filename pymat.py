import re
import sys
from collections import namedtuple
from io import BytesIO
from itertools import chain, compress, groupby
from operator import itemgetter
from tokenize import (COMMENT, ENCODING, ENDMARKER, NAME, NEWLINE, NL, NUMBER,
                      OP, tokenize, untokenize)

from IPython.core.inputtransformer import TokenInputTransformer

TokenInfoShort = namedtuple('TokenInfoShort', ['type', 'string'])

def identify_mat(tokens):
    groups, selectors = [], []
    is_number_newline_commment_semicolon = lambda x: x[1].type in [NUMBER, NL, COMMENT] or (x[1].type == OP and x[1].string == ';')
    for s, g in groupby(enumerate(tokens), is_number_newline_commment_semicolon):
        maybe_mat = list(filter(lambda t: t[1].type in [NUMBER, OP, NL], g))
        if [t.type for _, t in maybe_mat].count(NUMBER) > 1:
            groups.append(maybe_mat)
            selectors.append(s)
    selects = []
    for group in compress(groups, selectors):
        if len(group) > 1:
            beg, end = group[0][0], group[-1][0] + 1 # end is one element behind the last
            left, right = tokens[beg-1], tokens[end] # include surrounding square brackets '[' and ']' if there are any
            if (left.type, left.string) == (OP, '[') and (right.type, right.string) == (OP, ']'): 
                beg -= 1
                end += 1
            selects.append(slice(beg, end))
    return selects

def replace_mat(tokens, selects):
    result = tokens[:]
    for select in reversed(selects): # run backwards not to mess up by chaning
        mat_tok = [(ENCODING, 'utf-8')] + tokens[select] + [(ENDMARKER, '')] # add encoding info
        mat_cmd = untokenize(mat_tok).decode('utf-8').replace('\n', ' ')
        mat_cmd = 'numpy.array(numpy.mat("{}"))'.format(mat_cmd)
        mat_cmd = re.sub(r'\[\s*(.*?)\s*\]', r'[\g<1>]', mat_cmd)
        if ';' not in mat_cmd: #means single dimentional array so extract first elemetn
            mat_cmd += '[0]'
        mat_tok = tokenize(BytesIO(mat_cmd.encode('utf_8')).readline)
        result[select] = [TokenInfoShort(t.type, t.string) for t in mat_tok][1:-1] # [1:-1] remove encoding info and ENDMARKER tokens
    return result

@TokenInputTransformer.wrap
def mat_transformer(tokens):
    tokens = list(filter(lambda t: t.type != NL, tokens)) # fix multiline issue
    selects = identify_mat(tokens)
    if selects:
        tokens = [TokenInfoShort(t.type, t.string) for t in tokens]
        tokens = replace_mat(tokens, selects)
        if 'numpy' not in sys.modules:
            tokens = [(NAME, 'import'), (NAME, 'numpy'), (OP, ';')] + tokens
    return tokens

_extension = None
def load_ipython_extension(ip):
    global _extension
    _extension = mat_transformer()
    for s in (ip.input_splitter, ip.input_transformer_manager):
        s.python_line_transforms.extend([_extension])
    print('loaded:', __name__)

def unload_ipython_extension(ip):
    for s in (ip.input_splitter, ip.input_transformer_manager):
        s.python_line_transforms.remove(_extension)
    print('unloaded:', __name__)
