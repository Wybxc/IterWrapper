from collections import Iterable as _Iterable


class IterWrapper:
    """
    A wrapper for any Iterable, to describe a Functional Programming
    style for python to deal with Iterables.

    The wrapped iter is lazy, and evertying done through the wrapper
    lazy too, so you need to specify a \n 
    consumer to make the wrapper output everything, 
    like `IterWrapper.exhaust()` or `IterWrapper.collect()`

    The wrapped iterator can be iterated as original.

    Parameters
    ----------
    it : any iterables that is instance of `Iterable`, use for
    IterWrapper to know what should it wrap into.

    Examples
    --------
    ```python
    >>> it = IterWrapper(range(0,10))
    >>> for i in it:
            print(i) # prints 0 to 9
    ```

    Indexing And Slicing
    --------------------
    IterWrapper has its support for indexing and slicing, also
    implemented an special mechanism for iterators that not
    originally support indexing and slicing :

    ```python
    >>> IterWrapper([1,2,3])[1]
    2
    >>> IterWrapper([1,2,3])[:-1].unwrap()
    [1,2]
    >>> IterWrapper({'a': 'b'})['a']
    'b'
    >>> IterWrapper({x : x+1 for x in range(10)})[1:2:3].collect(list)
    [1,4]
    >>> IterWrapper(range(0, 10))[5]
    4
    ```

    Notice that dict() is not a sliceable object,
    so Wrapper converts the slicing to `iter.skip(start).step(step).take(stop)`,
    it means that the [1:2:3] will skip the first 1 item, and take the 2 items
    remained in the generator by step 3.


    Operand
    -------
    Serveral operands are overriden to make the manipulation easier and more
    readable.

    ```python
    >>> i1 = IterWrapper([1,2,3])
    >>> (i1 + [4,5,6]).collect(list) # => i1.chain([4, 5, 6])
    [1, 2, 3, 4, 5, 6]
    >>> (i1 * 3).collect(list) # => i1.repeat(3)
    [1, 2, 3, 1, 2, 3, 1, 2, 3]
    >>> (i1 | (lambda x : x+1) | print).exhaust()
    >>> # => i1.map(lambda x : x + 1).map(print)
    2
    3
    4
    >>> 1 in i1
    True
    >>> 4 in i1
    False
    >>> from iters import IterWrapper as iw
    iw([1,2]).collect(list)
    ```
    """

    def __init__(self, it):
        super().__init__()
        if not isinstance(it, _Iterable):
            raise TypeError

        self.__iterable__ = it

    def __iter__(self):
        return self.__iterable__.__iter__()

    def __len__(self):
        return len(self.__iterable__)

    def __getitem__(self, index):
        if isinstance(index, slice):
            try:
                return IterWrapper(self.__iterable__[index])
            except:
                if index.start < 0 or index.step < 1 or index.stop < 0:
                    raise ValueError("Unsupported slicing conversion for iterable")
                return self.skip(index.start).step(index.step).take(index.stop)
        else:
            try:
                return self.__iterable__[index]
            except:
                if type(index) is int:
                    return self.skip(index).take(1).collect(list)[0]
                else:
                    raise IndexError("Unsupported indexing for iterable")

    def __add__(self, other):
        return self.chain(other)

    def __radd__(self, other):
        return self.chain(other, before=True)

    def __mul__(self, other):
        return self.repeat(other)

    def __rmul__(self, other):
        return self.repeat(other)

    def __or__(self, other):
        return self.map(other)

    def __contains__(self, obj):
        return self.contains(obj)

    def map(self, f):
        """
        Map the iterator by f(i). a wrapped version of the built-in method map().

        Parameters
        ----------
        f : callable that use to map the values

        Examples
        --------
        ```python
        >>> IterWrapper(range(0,10)).map(lambda x : x + 1).collect(list)
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        ```
        """

        return IterWrapper(map(f, self.__iterable__))

    def foreach(self, f):
        """
        Call f(n) for each item in the iterator, use to mutate item in the iterables,
        or do something while iterating without breaking the chain.

        This method does NOT return the result of f(), it returns n.

        Parameters
        ----------
        f : callable to call

        Examples
        --------
        ```python
        >>> IterWrapper([[1,2,3],[1,2],[1]]).foreach(list.pop).collect(list)
        [[1, 2], [1], []]
        ```
        """

        def closure():
            for i in self.__iterable__:
                f(i)
                yield i

        return IterWrapper(closure())

    def filter(self, f):
        """
        Filter the iterator by f(i). a wrapped version of the built-in method filter()

        Parameters
        ----------
        f : callable the use to filter the values

        Examples
        --------
        ```python
        >>> IterWrapper(range(0,10)).filter(lambda x : x%2 ==0).collect(list)
        [0, 2, 4, 6, 8]
        ```
        """
        return IterWrapper(filter(f, self.__iterable__))

    def flat(self):
        """
        Flatten the iterator by 1 depth.

        Examples
        --------
        ```python
        >>> IterWrapper(range(0,10)).map(lambda x : (x, x+1)).flat().collect(list)
        [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 7, 8, 8, 9, 9, 10, 10, 11]
        ```
        """

        def closure():
            for i in self.__iterable__:
                if isinstance(i, _Iterable):
                    for j in i:
                        yield j
                else:
                    yield i

        return IterWrapper(closure())

    def take(self, c):
        """
        Only yield the first c items in the iterator.

        Parameters
        ----------
        c : the count of items to return

        Examples
        --------
        ```python
        >>> IterWrapper(range(0,10)).take(5).collect(list)
        [0, 1, 2, 3, 4]
        ```
        """

        if c is None:
            return self

        def closure():
            for idx, i in enumerate(self.__iterable__):
                if idx + 1 > c:
                    break
                yield i

        return IterWrapper(closure())

    def skip(self, c):
        """
        Discard the first c items in the iterator.

        Parameters
        ----------
        c : the count of items to skip

        Examples
        --------
        ```python
        >>> IterWrapper(range(0,10)).skip(5).collect(list)
        [5, 6, 7, 8, 9]
        ```
        """
        if c is None:
            return self

        def closure():
            for idx, i in enumerate(self.__iterable__):
                if idx >= c:
                    yield i

        return IterWrapper(closure())

    def step(self, s):
        """
        Take the items in the iterator by step s.

        Parameters
        ----------
        s : the step

        Examples
        --------
        ```python
        >>> IterWrapper(range(0,10)).step(2).collect(list)
        [0, 2, 4, 6, 8]
        ```
        """
        if s is None:
            return self

        def closure():
            for idx, i in enumerate(self.__iterable__):
                if idx % s == 0:
                    yield i

        return IterWrapper(closure())

    def mutate(self, t, *args, **kwargs):
        """
        Mutate the iterable into another by casting to t(iter), 
        the mutated iterable is also wrapped.

        Parameters
        ----------
        t : the destination type, or a converter you want to mutate

        args : positional args for converter

        kwargs : keyword args
        
        Examples
        --------
        ```python
        >>> IterWrapper(range(0,10)).unwrap()
        range(0, 10)
        >>> IterWrapper(range(0,10)).mutate(list).unwrap()
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        >>> IterWrapper([3,1,4,2]).mutate(lambda x, t : t(x), list).unwrap()
        [3, 1, 4, 2]
        ```
        """

        return IterWrapper(t(self.__iterable__, *args, **kwargs))

    def chain(self, it, before=False):
        """
        Chain the wrapper with iterable.
        
        Parameters
        ----------
        it : the iterator to be chained

        before : if True, `it` will yield before wrapper

        Examples
        --------
        ```python
        >>> IterWrapper(range(1,6)).chain(range(6,0,-1)).collect(list)
        [1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1]
        ```
        """

        def closure():
            if before:
                yield from it
                yield from self.__iterable__
            else:
                yield from self.__iterable__
                yield from it

        return IterWrapper(closure())

    def repeat(self, t):
        """
        Repeat the wrapped iterator for given times, notice that it is
        exhaustive, since some iterable can only be yield for 1 time.

        Parameters
        ----------
        t : times

        Examples
        --------
        ```python
        >>> IterWrapper(range(1,4)).repeat(3).collect(list)
        [1, 2, 3, 1, 2, 3, 1, 2, 3]
        ```
        """

        def closure():
            for _ in range(t):
                yield from self.__iterable__

        return IterWrapper(closure())

    def chunk(self, n, t=tuple, d=None):
        """
        Return a generator of t(tuple) with size n default with d(None).
        
        Pipe a list of item with size n into the t, and returns the t(n).

        Parameters
        ----------
        n : size of tuple

        Examples
        --------
        ```python
        >>> IterWrapper([1,2,3,4,5]).chunk(2).collect(list)
        [(1,2), (3,4), (5,None)]
        ```
        """

        def closure():
            it = self.__iterable__.__iter__()
            remained = True
            while remained:
                r = []
                try:
                    for _ in range(n):
                        r.append(next(it))
                except StopIteration:
                    r += [d for _ in range(n - len(r))]
                    remained = False
                yield t(r)

        return IterWrapper(closure())

    def zip(self, *it):
        """
        Return a zipped iterator of iterables.
        
        A convinient wrapper of built-in function zip().
        """

        return IterWrapper(zip(self.__iterable__, *it))

    def inf(self):
        """
        Make the generator always try to yield from the iterable.

        The generator will stop if the iterable is exhausted and NOT recoverable.

        Use with caution.

        Example
        -------
        ```python
        >>> IterWrapper([1,2,3]).inf().take(10).collect(list)
        [1, 2, 3, 1, 2, 3, 1, 2, 3, 1]
        >>> IterWrapper(range(10)).filter(lambda x : x%2==0).inf().take(100).collect(list)
        [0, 2, 4, 6, 8] # The filter() was exhausted during the first iteration.
        
        >>> (IterWrapper(range(10))
            .filter(lambda x : x%2==0)
            .mutate(list)
            .inf()
            .take(10)
            .collect(list)
            )
        [0, 2, 4, 6, 8, 0, 2, 4, 6, 8]
        ```
        """

        def closure():
            it = self.__iterable__.__iter__()
            while True:
                try:
                    yield next(it)
                except StopIteration:
                    it = self.__iterable__.__iter__()
                    try:
                        yield next(it)
                    except StopIteration:
                        break

        return IterWrapper(closure())

    def fold(self, c, d=None):
        """
        Iteratively calls the increment method by input `incremental variable`
        and the item in the iterator, the returned value will be stored in the
        `incremental variable`.

        Parameters
        ----------
        c : the increment method

        d : the starting default value of the variable, defaulting to None.

        Examples
        --------
        ```python
        >>> IterWrapper(range(1,11)).fold(lambda c, x : c+x**2)
        385 # The sum of squares from 1 to 10
        ```
        """
        r = d
        for i in self.__iterable__:
            r = c(r, i)
        return r

    def unwrap(self):
        """
        Unwraps the iterable inside the wrapper.

        Examples
        --------
        ```python
        >>> IterWrapper([0, 1]).unwrap()
        [0, 1]
        ```
        """
        return self.__iterable__

    def collect(self, t):
        """
        Feed the iterable to t, and DIRECTLY return the casted value.

        Simliar to IterWrapper.mutate(t).unwrap().

        Parameters
        ----------
        t : the variable (mainly types) to consume the iterable

        Examples
        --------
        ```python
        >>> IterWrapper(range(0, 10)).collect(list)
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        >>> IterWrapper([0, 1]).collect(lambda it : [print(i) for i in it])
        0
        1
        [None, None]
        ```
        """
        return t(self.__iterable__)

    def pipe(self, f):
        """
        Iteratively feed items in iterable into the consumer f, this method is 
        exhaustive. 

        Similiar to IterWrapper.map(f).exhaust() or IterWrapper.fold(f), but
        much more dedicated as a end point consumer.

        Parameters
        ----------
        f : the consumer

        Examples
        --------
        ```python
        >>> IterWrapper([0, 1]).pipe(print)
        0
        1
        ```
        """
        for i in self.__iterable__:
            f(i)

    def apply(self, m, *args, **kwargs):
        """
        Apply a certain method to the iterable, the iterable is piped into the method m.

        Similar to IterWrapper.pipe(f), but the iterable is passed directly.

        This is used for chaining `IN-PLACE` methods like list.sort or something into the
        wrapper call.

        Parameters
        ----------
        m : the method applied to iterable

        args : the positional arguments to feed into the method

        kwargs : the keyword arguments

        Examples
        --------
        >>> IterWrapper([3,1,4,2]).apply(list.sort,reverse=True).unwrap()
        [4, 3, 2, 1]
        """

        m(self.__iterable__, *args, **kwargs)
        return self

    def exhaust(self):
        """
        Exhaust the iterator.

        No returns.

        Examples
        --------
        ```python
        >>> IterWrapper(range(0,3)).map(print).exhaust()
        0
        1
        2   
        ```
        """
        for i in self.__iterable__:
            pass

    def count(self, f=None):
        """
        Count the items in the iterable (by condition), this method is exhaustive.

        Parameters
        ----------
        f : the condition function

        Examples
        --------
        ```python
        >>> IterWrapper([0, 1]).count()
        2
        >>> IterWrapper([0, 1]).count(lambda x : x>0)
        1
        ```
        """
        if f is None:
            return len(self.collect(list))
        else:
            c = 0
            for i in self:
                if f(i):
                    c += 1
            return c

    def contains(self, item):
        """
        Check if given item is in the iterable, this method is exhaustive.

        Parameters
        ----------
        item : the item to check

        Examples
        --------
        ```python
        >>> IterWrapper([1, 2, 3]).contains(1)
        True
        >>> IterWrapper([1, 2, 3]).contains(8)
        False
        ```
        """
        for i in self.__iterable__:
            if i == item:
                return True
        return False

    def rev(self):
        """
        Reverse the iterable inside the wrapper, and will
        always return a list if the iterator is not sliceable.

        Examples
        -------
        ```python
        >>> IterWrapper(range(0,10)).rev().collect(list)
        [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
        ```
        """
        try:
            return IterWrapper(self.__iterable__[::-1])
        except:
            return self.mutate(list)[::-1]
