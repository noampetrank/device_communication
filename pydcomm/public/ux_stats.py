"""
Contains the class `metacollectstats` which is to be used as a metaclass for classes that you want to save ApiCall
summaries of.

There is also the class `ApiCallsRecorder` for usage in benchmarks.
"""

import time
from collections import namedtuple
from functools import wraps
from types import FunctionType

ApiCall = namedtuple("ApiCall", "class_name function_name start_time end_time manual_times "
                                "exception_type exception_msg is_exception")

api_stats = []
"""@type: list[ApiCall]"""


# noinspection PyBroadException
class ApiCallsRecorder(object):
    """
    Context manager that saves api calls in a member called `api_states`.
    This is in addition to calling the static method `save_api_call`, that will soon save them to the disk.
    Unless you chose to suspend the call to `save_api_call`.

    Example:
        >>> class foo(object):
        ...     __metaclass__ = metacollectstats  # See below.
        ...     def bar(self):
        ...         raise NotImplementedError("Bummer")
        >>>
        >>> recorder = ApiCallsRecorder()
        >>> with recorder:
        ...     try: foo().bar()
        ...     except: pass
        >>>
        >>> assert len(recorder.api_stats) == 1
        >>> api_call = recorder.api_stats[0]
        >>> assert api_call.class_name == "foo"
        >>> assert api_call.function_name == "bar"
        >>> assert len(api_call.manual_times) == 0
        >>> assert api_call.is_exception
        >>> assert api_call.exception_type is NotImplementedError
        >>> assert api_call.exception_msg == "Bummer"
    """
    @staticmethod
    def save_api_call(api_call):
        """
        Saves `api_call`. Currently in a global variable.

        TODO: Save data to disk.

        :param ApiCall api_call: Data to save.
        """
        api_stats.append(api_call)

    def __init__(self, suspend_save=False):
        """
        :param bool suspend_save: Whether or not to also call original `save_api_call` that (not yet) saves to disk.
        """
        self.suspend_save = suspend_save
        self.api_stats = []
        self._orig_save_api_call = None

    def __enter__(self):
        self._orig_save_api_call = ApiCallsRecorder.save_api_call

        def new_save_api_call(api_call):
            self.api_stats.append(api_call)
            if not self.suspend_save:
                self._orig_save_api_call(api_call)

        ApiCallsRecorder.save_api_call = staticmethod(new_save_api_call)

    def __exit__(self, exc_type, exc_val, exc_tb):
        ApiCallsRecorder.save_api_call = staticmethod(self._orig_save_api_call)


_fake_sentinel = object()


def collectstats(class_name=None):
    """
    Decorator for functions to collect call stats. For each recursive sequence of calls, the top decorated function, and
    only that function, is saved after returning by calling `save_api_call` with the stats.

    Example:
        >>> @collectstats("no class!")
        ... def foo():
        ...     raise NotImplementedError("never will be :)")
        >>> try:
        ...     foo()
        ... except NotImplementedError:
        ...     api_call = api_stats[-1]
        ...     assert api_call.class_name == "no class!"
        ...     assert api_call.function_name == "foo"
        ...     assert api_call.manual_times == []
        ...     assert api_call.exception_type is NotImplementedError
        ...     assert api_call.exception_msg == "never will be :)"
        ...     assert api_call.is_exception

    :param class_name: Name of class
    """
    def inner(func):
        funcname = func.__name__

        @wraps(func)
        def newfunc(*args, **kwargs):
            import __builtin__
            orig = __builtin__.raw_input

            if getattr(orig, "_UserExperienceStats_fake", None) is not _fake_sentinel:
                start = time.time()
                manual_times = []
                exception_type = None
                exception_msg = None
                is_exception = False

                def fake_raw_input(*args_, **kwargs_):
                    manual_start = time.time()
                    try:
                        return orig(*args_, **kwargs_)
                    finally:
                        manual_times.append((manual_start, time.time()))

                fake_raw_input._UserExperienceStats_fake = _fake_sentinel
                __builtin__.raw_input = fake_raw_input

                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    is_exception = True
                    exception_type = type(e)
                    exception_msg = e.message
                    raise
                finally:
                    __builtin__.raw_input = orig
                    end = time.time()
                    ApiCallsRecorder.save_api_call(ApiCall(class_name, funcname, start, end, manual_times,
                                                           exception_type, exception_msg, is_exception))
            else:
                return func(*args, **kwargs)

        return newfunc
    return inner


# noinspection PyUnresolvedReferences,PyMethodMayBeStatic
def decorateallfuncs(wrapper):
    """
        Creates a metaclass that decorates all generated classes' functions with `wrapper`.
        `wrapper` must be a function that takes a class name and returns a decorator.
        A Class whose metaclass is the result of `decorateallfuncs` will have all its methods decorated by
        `wrapper(class name)`. Inner classes' methods are also decorated.

        Example:
            >>> def printhello(class_name):
            ...     def inner(func):
            ...         @wraps(func)
            ...         def newfunc(*args, **kwargs):
            ...             print "hello from", class_name
            ...             try: return func(*args, **kwargs)
            ...             finally:
            ...                 print "goodbye!"
            ...         return newfunc
            ...     return inner
            >>> class foo(object):
            ...     __metaclass__ = decorateallfuncs(printhello)
            ...     def __init__(self):
            ...         print "ok init foo."
            ...     def method(self):
            ...         print "ok method."
            ...     @staticmethod
            ...     def sttcmethod():
            ...         print "ok staticmethod."
            ...     @classmethod
            ...     def clsmethod(cls):
            ...         print "ok classmethod."
            ...     class inner(object):
            ...         def innerclass(self):
            ...             print "ok innerclass."
            >>> f = foo()
            hello from foo
            ok init foo.
            goodbye!
            >>> f.method()
            hello from foo
            ok method.
            goodbye!
            >>> f.sttcmethod()
            hello from foo
            ok staticmethod.
            goodbye!
            >>> f.clsmethod()
            hello from foo
            ok classmethod.
            goodbye!
            >>> f.inner().innerclass()
            hello from inner
            ok innerclass.
            goodbye!
            >>> class bar(foo):
            ...     def __init__(self):
            ...         super(bar, self).__init__()
            ...         print "ok init inheritance."
            ...     def inheritance(self):
            ...         print "ok inheritance."
            >>> bar().inheritance()
            hello from bar
            hello from foo
            ok init foo.
            goodbye!
            ok init inheritance.
            goodbye!
            hello from bar
            ok inheritance.
            goodbye!

        :param wrapper: Decorator to use.
        :return type: Metaclass.
        """
    wrapper_id = id(wrapper)

    class DecorateAllCalls(type):
        _DecorateAllCalls_wrapper = wrapper_id

        def __new__(mcs, name, bases, class_dict):
            inner_wrapper = wrapper(name)

            new_class_dict = {}
            for attrname, attr in class_dict.items():
                if isinstance(attr, FunctionType):
                    attr = inner_wrapper(attr)
                elif isinstance(attr, staticmethod):
                    attr = staticmethod(inner_wrapper(attr.__func__))
                elif isinstance(attr, classmethod):
                    attr = classmethod(inner_wrapper(attr.__func__))
                elif isinstance(attr, type):
                    if getattr(attr, "_DecorateAllCalls_wrapper", None) is not wrapper_id:
                        attr = mcs.__new__(mcs, attr.__name__, attr.__bases__, attr.__dict__)
                new_class_dict[attrname] = attr

            return type.__new__(mcs, name, bases, new_class_dict)

    return DecorateAllCalls


# Use this metaclass to collect stats on all calls to a class's methods.
metacollectstats = decorateallfuncs(collectstats)


def test_metacollectstats():
    """
    Tests `metacollectstats`!
    Sets a three class hierarchy with the base marked with `metacollectstats`, then calls three functions, two of which
    raise exceptions and call `raw_input`, and one benign function.
    Test checks that three api calls are recorded with the correct attributes.
    """
    import mock
    import __builtin__

    class foo(object):
        __metaclass__ = metacollectstats

        def bar(self):
            raise RuntimeError("Hello, {}!".format(raw_input("name:")))

    class baz(foo):
        def bar(self):
            super(baz, self).bar()

    class shunga(baz):
        def tzunga(self):
            pass
    
    @mock.patch.object(__builtin__, "raw_input")
    def call_bar(cls_, name, mraw_input):
        mraw_input.return_value = name
        cls_().bar()

    recorder = ApiCallsRecorder()
    with recorder:
        try:
            call_bar(foo, "World")
        except RuntimeError:
            pass
        else:
            raise RuntimeError("Should've raised here")

        try:
            call_bar(baz, "and goodbye")
        except RuntimeError:
            pass
        else:
            raise RuntimeError("Should've raised here")

        shunga().tzunga()

    assert len(recorder.api_stats) == 3

    api_call = recorder.api_stats[0]  # type: ApiCall
    assert api_call.class_name == "foo"
    assert api_call.function_name == "bar"
    assert len(api_call.manual_times) == 1
    assert api_call.is_exception
    assert api_call.exception_type is RuntimeError
    assert api_call.exception_msg == "Hello, World!"

    api_call = recorder.api_stats[1]  # type: ApiCall
    assert api_call.class_name == "baz"
    assert api_call.function_name == "bar"
    assert len(api_call.manual_times) == 1
    assert api_call.is_exception
    assert api_call.exception_type is RuntimeError
    assert api_call.exception_msg == "Hello, and goodbye!"

    api_call = recorder.api_stats[2]  # type: ApiCall
    assert api_call.class_name == "shunga"
    assert api_call.function_name == "tzunga"
    assert len(api_call.manual_times) == 0
    assert not api_call.is_exception
    assert api_call.exception_msg is None


if __name__ == '__main__':
    test_metacollectstats()
