import re
import sys
from io import BytesIO
from itertools import chain, compress, groupby
from operator import itemgetter
from tokenize import (COMMENT, ENCODING, ENDMARKER, NAME, NEWLINE, NL, NUMBER,
                      OP, tokenize, untokenize)

from IPython.core.inputtransformer import TokenInputTransformer

def _index_numpy_mat_tokens(tokens):
    groups, selectors = [], []
    group_numpy_mat_expression = lambda t: t.type in [NUMBER, NL, COMMENT] or (t.type == OP and t.string == ';')
    for s, g in groupby(enumerate(tokens), lambda x: group_numpy_mat_expression(x[1]) ):
        maybe_mat = list(filter(lambda t: t[1].type in [NUMBER, OP, NL], g))
        if [t.type for _, t in maybe_mat].count(NUMBER) > 1:
            groups.append(maybe_mat)
            selectors.append(s)
    return compress(groups, selectors)

def identify_mat(tokens):
    indexed_tokens = _index_numpy_mat_tokens(tokens)
    selects = []
    for group in indexed_tokens:
        if len(group) > 1:
            beg, end = group[0][0], group[-1][0] + 1 # end is one element behind the last
            if beg > 0 and end < len(tokens): # include surrounding square brackets '[' and ']' if there are any, TODO: move to _index_numpy_mat_tokens function
                left, right = tokens[beg-1], tokens[end] 
                if (left.type, left.string) == (OP, '[') and (right.type, right.string) == (OP, ']'): 
                    beg -= 1
                    end += 1
            selects.append(slice(beg, end))
    return selects

def _str2tokens(s):
    return list(tokenize(BytesIO(s.encode('utf_8')).readline))[1:-1] # [1:-1] remove ENCODING and ENDMARKER tokens (first and last tokens)

def replace_mat(tokens, selects):
    result = tokens[:]
    for select in reversed(selects): # run backwards not to mess up by chaning
        mat_tok = [(ENCODING, 'utf-8')] + tokens[select] + [(ENDMARKER, '')] # add encoding info
        mat_cmd = untokenize(mat_tok).decode('utf-8').replace('\n', ' ')
        mat_cmd = 'numpy.array(numpy.mat("{}"))'.format(mat_cmd)
        mat_cmd = re.sub(r'\[\s*(.*?)\s*\]', r'[\g<1>]', mat_cmd)
        if ';' not in mat_cmd: #means single dimentional array so extract first elemetn
            mat_cmd += '[0]'
        result[select] = _str2tokens(mat_cmd)
    return result

@TokenInputTransformer.wrap
def mat_transformer(tokens):
    tokens = list(filter(lambda t: t.type != NL, tokens)) # fix multiline issue
    selects = identify_mat(tokens)
    if selects:
        tokens = replace_mat(tokens, selects)
        if 'numpy' not in sys.modules:
            tokens = _str2tokens('import numpy;') + tokens
        else:
            try: # required when numpy is imported as np before extension is loaded - most of the time it is loaded as np
                exec('numpy')
            except NameError:
                tokens = _str2tokens('import sys;numpy=sys.modules["numpy"];')  + tokens
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
