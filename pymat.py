from IPython.core.inputtransformer import TokenInputTransformer

from tokenize import tokenize, untokenize, ENCODING, NEWLINE, NAME, ENDMARKER, NUMBER, OP, NL, COMMENT
from io import BytesIO
from itertools import groupby
from collections import namedtuple
import re

MatTokenSelection = namedtuple('MatTokenSelection', ['begin', 'end'])
TokenInfoShort = namedtuple('TokenInfoShort', ['type', 'string'])
def identify_mat(tokens):
    tokens[0]
    results = []
    g = groupby(enumerate(tokens), lambda x: x[1].type in [NUMBER, NL, COMMENT] or 
                                            (x[1].type == OP and x[1].string == ';'))
    for test, group in g:
        group = list(group)
        if test and len(group) > 1:
            beg_idx = group[0][0]
            end_idx = group[-1][0] + 1
            if tokens[beg_idx-1].type == OP and tokens[beg_idx-1].string == '[' : beg_idx -= 1
            if tokens[end_idx].type == OP and tokens[end_idx].string == ']' : end_idx += 1
            results.append(MatTokenSelection(beg_idx, end_idx))
    return results

def replace_mat(tokens, selects):
    result = tokens[:]
    for beg, end in reversed(selects):
        select = [(ENCODING, 'utf-8')] + tokens[beg:end] + [(ENDMARKER, '')]
        mat_command = untokenize(select).decode('utf-8')
        mat_command = "numpy.array(numpy.mat('''{}'''))".format(mat_command).replace('\n', ' ')
        mat_command = re.sub(r'\[\s*', '[', mat_command)
        mat_command = re.sub(r'\s*\]', ']', mat_command)
        if ';' not in mat_command:
            mat_command += '[0]'
        result[beg:end] = [TokenInfoShort(t,v) for t,v,_,_,_ in list(tokenize(BytesIO(mat_command.encode('utf_8')).readline))[1:-1]]
    return result

@TokenInputTransformer.wrap
def mat_transformer(tokens):
    tokens = [TokenInfoShort(NAME, 'import'), TokenInfoShort(NAME, 'numpy'), TokenInfoShort(OP, ';') ] + [TokenInfoShort(t,v) for t,v,_,_,_ in tokens]
    #tokens = [TokenInfoShort(t,v) for t,v,_,_,_ in tokens]
    selects = identify_mat(tokens)
    tokens = replace_mat(tokens, selects)
    return tokens

_extension = None

# def load_ipython_extension(ip):
#     for s in (ip.input_splitter, ip.input_transformer_manager):
#         s.python_line_transforms.extend([mat_transformer()])
#     print('loaded:', __name__)

def load_ipython_extension(ip):
    global _extension
    _extension = mat_transformer()
    for s in (ip.input_splitter, ip.input_transformer_manager):
        s.python_line_transforms.extend([_extension])
    print('loaded:', __name__)


def unload_ipython_extension(ip):
    for s in (ip.input_splitter, ip.input_transformer_manager):
        print (_extension)
        s.python_line_transforms.remove(_extension)
    print('unloaded:', __name__)
