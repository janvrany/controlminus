# Copyright (c) 2020 Jan Vrany <jan.vrany (a) fit.cvut.cz>
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
from types import MethodType as __bind
from inspect import iscoroutinefunction as __iscoroutine

def __wrap(old, new):
    setattr(old.__self__, old.__name__, __bind(new, old.__self__))


def before(bound_method):
    def decorator(func):
        if __iscoroutine(bound_method):
            async def wrapper(recv, *args):
                if __iscoroutine(func):
                    await func(recv, *args)
                else:
                    func(recv, *args)
                return await bound_method(*args)
            __wrap(bound_method, wrapper)
        else:
            def wrapper(recv, *args):
                func(recv, *args)
                return bound_method(*args)
            __wrap(bound_method, wrapper)
    return decorator

def after(bound_method):
    def decorator(func):
        if __iscoroutine(bound_method):
            async def wrapper(recv, *args):
                retval = await bound_method(*args)
                if __iscoroutine(func):
                    await func(recv, *args)
                else:
                    func(recv, *args)
                return retval
            __wrap(bound_method, wrapper)
        else:
            def wrapper(recv, *args):
                retval = bound_method(*args)
                func(recv, *args)
                return retval
            __wrap(bound_method, wrapper)
    return decorator