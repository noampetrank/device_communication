"""
Contains the class `metacollectstats` which is to be used as a metaclass for classes that you want to save ApiCall
summaries of.

There is also the class `ApiCallsRecorder` for usage in benchmarks.
"""
import os
import time
import json
from collections import namedtuple
from functools import wraps
from types import FunctionType

ApiCall = namedtuple("ApiCall", "class_name function_name start_time end_time manual_times "
                                "exception_type exception_msg is_exception args kwargs ret extra_stats")

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
        ...     def __extra_stats__(self):
        ...         return {'x': 8}
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
        >>> assert api_call.exception_type == 'NotImplementedError'
        >>> assert api_call.exception_msg == "Bummer"
        >>> assert api_call.extra_stats == {'x':8}
    """
    @staticmethod
    def _get_save_file():
        # TODO: remove pybuga dependency
        from pybuga.infra.utils.config import get_tmp_dir_path

        return open(os.path.join(get_tmp_dir_path(), "ux_stats.jsons"), "a")

    @staticmethod
    def save_api_call(api_call):
        """
        Saves `api_call`. Currently in a global variable.

        :param ApiCall api_call: Data to save.
        """
        def arg_to_str(x):
            max_len = 200
            sx = repr(x)
            if len(sx) > max_len:
                sx = sx[:max_len] + "..."
            return sx

        s_args = map(arg_to_str, api_call.args)
        s_kwargs = {k: arg_to_str(v) for k, v in api_call.kwargs.items()}
        s_ret = arg_to_str(api_call.ret)
        api_call = api_call._replace(args=s_args, kwargs=s_kwargs, ret=s_ret)

        api_stats.append(api_call)

        with ApiCallsRecorder._get_save_file() as f:
            json.dump(api_call._asdict(), f)
            f.write("\n")

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


def collectstats(class_name=None, collect_extra=False):
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
        ...     assert api_call.exception_type == 'NotImplementedError'
        ...     assert api_call.exception_msg == "never will be :)"
        ...     assert api_call.is_exception
        ...     assert api_call.extra_stats is None

    :param class_name: Name of class
    :param bool collect_extra: If you pass True, collectstats will check if there is a __extra_stats__(self) method
                               defined on the first passed argument (which for instance methods should be self),
                               and execute it to get more stats to be collected.
                               __extra_stats__ should return a dict of such stats.
    """
    from pybuga.infra.utils.buga_utils import argwraps

    def inner(func):
        funcname = func.__name__

        @argwraps(func)
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

                extra_stats = None
                if collect_extra and len(args) > 0:
                    extra_stats = getattr(args[0], "__extra_stats__", None)
                extra_data = None
                ret = None

                try:
                    ret = func(*args, **kwargs)
                    if extra_stats is not None:
                        extra_data = extra_stats()
                    return ret
                except Exception as e:
                    is_exception = True
                    exception_type = type(e).__name__
                    exception_msg = e.message
                    raise
                finally:
                    __builtin__.raw_input = orig
                    end = time.time()

                    ApiCallsRecorder.save_api_call(ApiCall(class_name, funcname, start, end, manual_times,
                                                           exception_type, exception_msg, is_exception,
                                                           args, kwargs, ret, extra_data))
            else:
                return func(*args, **kwargs)

        return newfunc
    return inner


# noinspection PyUnresolvedReferences,PyMethodMayBeStatic
def decorateallfuncs(wrapper):
    """
        Creates a metaclass that decorates all generated classes' functions with `wrapper`.
        `wrapper` must be a function that takes a class name and boolean stating whether this is an instance
        method and returns a decorator.
        A Class whose metaclass is the result of `decorateallfuncs` will have all its methods decorated by
        `wrapper(class_name, is_inst_method)`. Inner classes' methods are also decorated.

        Example:
            >>> def printhello(class_name, is_inst_method):
            ...     def inner(func):
            ...         @wraps(func)
            ...         def newfunc(*args, **kwargs):
            ...             print "hello from", class_name, is_inst_method
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
            hello from foo True
            ok init foo.
            goodbye!
            >>> f.method()
            hello from foo True
            ok method.
            goodbye!
            >>> f.sttcmethod()
            hello from foo False
            ok staticmethod.
            goodbye!
            >>> f.clsmethod()
            hello from foo False
            ok classmethod.
            goodbye!
            >>> f.inner().innerclass()
            hello from inner True
            ok innerclass.
            goodbye!
            >>> class bar(foo):
            ...     def __init__(self):
            ...         super(bar, self).__init__()
            ...         print "ok init inheritance."
            ...     def inheritance(self):
            ...         print "ok inheritance."
            >>> b = bar()
            hello from bar True
            hello from foo True
            ok init foo.
            goodbye!
            ok init inheritance.
            goodbye!
            >>> b.inheritance()
            hello from bar True
            ok inheritance.
            goodbye!

        :param wrapper: Decorator to use.
        :return type: Metaclass.
        """
    wrapper_id = id(wrapper)

    class DecorateAllCalls(type):
        _DecorateAllCalls_wrapper = wrapper_id

        def __new__(mcs, name, bases, class_dict):
            new_class_dict = {}
            for attrname, attr in class_dict.items():
                if isinstance(attr, FunctionType):
                    inner_wrapper = wrapper(name, True)
                    attr = inner_wrapper(attr)
                elif isinstance(attr, staticmethod):
                    inner_wrapper = wrapper(name, False)
                    attr = staticmethod(inner_wrapper(attr.__func__))
                elif isinstance(attr, classmethod):
                    inner_wrapper = wrapper(name, False)
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

    class foo2(object):
        __metaclass__ = metacollectstats

        def __extra_stats__(self):
            return {"my_extra": 8}

        def bar(self):
            pass

        @staticmethod
        def baz(x):
            pass

        @classmethod
        def bax(cls):
            pass

    @collectstats()
    def im_a_pure_func(x):
        return x

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

        foo2().bar()

        foo2.baz(1)

        foo2.bax()

        im_a_pure_func(2)

    api_calls_iter = iter(recorder.api_stats)

    api_call = api_calls_iter.next()  # type: ApiCall
    assert api_call.class_name == "foo"
    assert api_call.function_name == "bar"
    assert len(api_call.manual_times) == 1
    assert api_call.is_exception
    assert api_call.exception_type == 'RuntimeError'
    assert api_call.exception_msg == "Hello, World!"
    assert api_call.extra_stats is None

    api_call = api_calls_iter.next()  # type: ApiCall
    assert api_call.class_name == "baz"
    assert api_call.function_name == "bar"
    assert len(api_call.manual_times) == 1
    assert api_call.is_exception
    assert api_call.exception_type == 'RuntimeError'
    assert api_call.exception_msg == "Hello, and goodbye!"
    assert api_call.extra_stats is None

    api_call = api_calls_iter.next()  # type: ApiCall
    assert api_call.class_name == "shunga"
    assert api_call.function_name == "tzunga"
    assert len(api_call.manual_times) == 0
    assert not api_call.is_exception
    assert api_call.exception_msg is None
    assert api_call.extra_stats is None

    api_call = api_calls_iter.next()  # type: ApiCall
    assert api_call.class_name == "foo2"
    assert api_call.function_name == "bar"
    assert api_call.extra_stats == {"my_extra": 8}

    api_call = api_calls_iter.next()  # type: ApiCall
    assert api_call.class_name == "foo2"
    assert api_call.function_name == "baz"
    assert api_call.extra_stats is None

    api_call = api_calls_iter.next()  # type: ApiCall
    assert api_call.class_name == "foo2"
    assert api_call.function_name == "bax"
    assert api_call.extra_stats is None

    api_call = api_calls_iter.next()  # type: ApiCall
    assert api_call.class_name is None
    assert api_call.function_name == "im_a_pure_func"
    assert api_call.extra_stats is None

    try:
        api_calls_iter.next()
        assert False
    except StopIteration:
        pass


if __name__ == '__main__':
    test_metacollectstats()
