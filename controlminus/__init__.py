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

from asyncio import _set_running_loop
from glibcoro import GLibEventLoop, GLibEventLoopPolicy

class GTKEventLoop(GLibEventLoop):
    def run_until_complete(self, future):
        raise Exception("Not supported - use be_running() to mark the loop as running followed by create_task()")

    def run_forever(self, future):
        raise Exception("Not supported - use be_running() to mark the loop as running")

    def be_running(self) :
        self._check_closed()
        assert self._gloop == None, "loop already running"        
        self._gloop = object()
        _set_running_loop(self)
    
    def is_running(self):
        return self._gloop != None

    def stop(self):
        raise Exception("Not supported")      


class GTKEventLoopPolicy(GLibEventLoopPolicy):
    def new_event_loop(self) :
        self._check_is_main_thread()
        return GTKEventLoop()



if __name__ == '__main__':    
    import asyncio
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk

    async def tick_tack_loop():
        async def tick_tack():
            print("tick")
            await asyncio.sleep(1)
            print("tack")
            await asyncio.sleep(1)
        while True:
            await tick_tack()

    asyncio.set_event_loop_policy(GTKEventLoopPolicy())
    asyncio.get_event_loop().create_task(tick_tack_loop())
    asyncio.get_event_loop().be_running()

    win = Gtk.Window()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
