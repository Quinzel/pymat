# pymat
ipython extension: Matlab, Octave syntax in ipython interpretter and jupyter notebook
array syntax from matlab is coverted into numpy.arrays.

```sh
In [1]: %load_ext pymat
loaded: pymat

# In [2]: A, B, C, D = 1 2 3, 1; 2; 3, [1 2 3], [1 2; 3 4; 5 6]

In [3]: A
Out[3]: array([1, 2, 3])

In [4]: B
Out[4]:
array([[1],
       [2],
       [3]])

In [5]: C
Out[5]: array([1, 2, 3])

In [6]: D
Out[6]:
array([[1, 2],
       [3, 4],
       [5, 6]])
       
In [7]: E = [1 2 3;
   ...: 4 5 6;
   ...: 7 8 9]
   ...:

In [8]: E
Out[8]:
array([[1, 2, 3],
       [4, 5, 6],
       [7, 8, 9]])
```
