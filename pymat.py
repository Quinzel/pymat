import re
import sys
from collections import namedtuple
from io import BytesIO
from itertools import chain, compress, groupby
from operator import itemgetter
from tokenize import (COMMENT, ENCODING, ENDMARKER, NAME, NEWLINE, NL, NUMBER,
                      OP, tokenize, untokenize)

from IPython.core.inputtransformer import TokenInputTransformer

Selection = namedtuple('Selection', ['begin', 'end'])
TokenInfoShort = namedtuple('TokenInfoShort', ['type', 'string'])

def identify_mat(tokens):
    groups, selectors = [], []
    is_number_newline_commment_semicolon = lambda x: x[1].type in [NUMBER, NL, COMMENT] or (x[1].type == OP and x[1].string == ';')
    for s, g in groupby(enumerate(tokens), is_number_newline_commment_semicolon):
        maybe_mat = list(filter(lambda t: t[1].type in [NUMBER, OP, NL], g))
        if [t for _, (t, _) in maybe_mat].count(NUMBER) > 1:
            groups.append(maybe_mat)
            selectors.append(s)
    
    selection = []
    for group in compress(groups, selectors):
        if len(group) > 1:
            beg, end = group[0][0], group[-1][0] + 1 # end is one element behind the last
            if tokens[beg-1] == (OP, '[') and tokens[end] == (OP, ']'): #include surrounding braces 
                beg -= 1
                end += 1
            selection.append(Selection(beg, end))
    return selection

def replace_mat(tokens, selects):
    result = tokens[:]
    for beg, end in reversed(selects): # run backwards not to mess up by chaning
        select = [(ENCODING, 'utf-8')] + tokens[beg:end] + [(ENDMARKER, '')] # add encoding info
        mat_cmd = untokenize(select).decode('utf-8').replace('\n', ' ')
        mat_cmd = 'numpy.array(numpy.mat("{}"))'.format(mat_cmd)
        mat_cmd = re.sub(r'\[\s*(.*?)\s*\]', r'[\g<1>]', mat_cmd)
        if ';' not in mat_cmd: #means single dimentional array so extract first elemetn
            mat_cmd += '[0]'
        mat_tok = map(itemgetter(0, 1), tokenize(BytesIO(mat_cmd.encode('utf_8')).readline))
        result[beg:end] = [TokenInfoShort(*t) for t in mat_tok][1:-1] # [1:-1] remove encoding info and ENDMARKER tokens
    return result

@TokenInputTransformer.wrap
def mat_transformer(tokens):
    oryginal_tokens = tokens[:]
    if 'numpy' not in sys.modules:
        tokens = [(NAME, 'import'), (NAME, 'numpy'), (OP, ';')] + tokens
    TokenInfoShortGetter = map(itemgetter(0, 1), tokens)
    tokens = [TokenInfoShort(t, s) for t, s in TokenInfoShortGetter]
    selects = identify_mat(tokens)
    if selects:
        tokens = replace_mat(tokens, selects)
    else:
        tokens = oryginal_tokens
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
