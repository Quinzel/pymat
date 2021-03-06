import pytest

from tokenize import tokenize, untokenize, NUMBER
from io import BytesIO
from functools import partial

from pymat import identify_mat, replace_mat



def ipython_tokenize_symulation(s): # same as pymat._str2tokens
    return list(tokenize(BytesIO(s.encode('utf_8')).readline))[1:-1] # [1:-1] remove ENCODING and ENDMARKER tokens (first and last tokens)

def ipython_untokenize_symulation(t): # same as pymat._tokens2str
    return untokenize(t).decode('utf-8')  

def test_identify_mat():
    test_fun = lambda x: identify_mat(ipython_tokenize_symulation(x))
    assert test_fun('a = 1, 2') == []
    assert test_fun('a = [1, 2]') == []
    assert test_fun('a = (1, 2), [1, 2], "asdf"') == [] 
    assert test_fun('a = 1 2')[0] == slice(2, 4)
    assert test_fun('a = [1 2]')[0] == slice(2, 6)
    assert test_fun('a = [1;2]')[0] == slice(2, 7)
    assert test_fun('a = [1; 2; 3]')[0] == slice(2, 9)
    assert test_fun('a = [1;\n2;\n3]')[0] == slice(2, 11)

def test_identify_mat_multi():
    test_fun = lambda x: identify_mat(ipython_tokenize_symulation(x))
    assert test_fun('a = 1 2, 1 2') == [slice(2, 4) , slice(5, 7)]
    assert test_fun('a = 1 2, (1, 2), 3, [1 2 3], [1, 2, 3], 1 2; 3 4') == [slice(2, 4) , slice(13, 18), slice(27, 32)]
    
def test_replace_mat():
    pass # TODO finish test
    # def test_fun(x):
    #     return ipython_untokenize_symulation(replace_mat(ipython_tokenize_symulation(x), identify_mat(ipython_tokenize_symulation(x))))

    # assert eval(test_fun('a = 1 2')) == eval("a = numpy.array(numpy.mat('1 2'))[0]")

if __name__ == '__main__':
    pytest.main()