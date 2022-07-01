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


from bricknil.process import Process
from evdev import InputDevice, events, ecodes, list_devices


class DualShock3(Process):
    """
    This class implements interface to Sony Playstation 3
    Dual Shock controller
    """

    _properties_ = [
            "abs-l-x", # X of left thumbstick (in range <0,255>)
            "abs-l-y", # Y of left thumbstick (in range <0,255>)
            "abs-r-x", # X of right thumbstick (in range <0,255>)
            "abs-r-y" # Y of right thumbstick (in range <0,255>)
    ]

    _signals_ = [
        'button-press-event',
        'button-release-event'
    ]

    def __init__(self, evdevice = None):
        if evdevice == None:
            devices = [InputDevice(fn) for fn in list_devices()]
            for device in devices:
                if device.name == 'Sony PLAYSTATION(R)3 Controller':
                    evdevice = device.path
            if evdevice == None:
                raise Exception("No PS3 DualShock controller detected")
        super().__init__(evdevice)

        self.__dev = InputDevice(evdevice)

        self.__abs_l_x = 128
        self.__abs_l_y = 128
        self.__abs_r_x = 128
        self.__abs_r_y = 128

    def do_get_property(self, prop):
        if prop.name == 'abs-l-x':
            return self.__abs_l_x
        elif prop.name == 'abs-l-y':
            return self.__abs_l_y
        elif prop.name == 'abs-r-x':
            return self.__abs_r_x
        elif prop.name == 'abs-r-y':
            return self.__abs_r_y
        else:
            raise AttributeError('unknown property %s' % prop.name)

    def do_set_property(self, prop, value):
        if prop.name == 'abs-l-x':
            self.__abs_l_x = value
        elif prop.name == 'abs-l-y':
            self.__abs_l_y = value
        elif prop.name == 'abs-r-x':
            self.__abs_r_x = value
        elif prop.name == 'abs-r-y':
            self.__abs_r_y = value
        else:
            raise AttributeError('unknown property %s' % prop.name)

    async def dispatch(self):
        async for ev in self.__dev.async_read_loop():
            if ev.type == events.EV_ABS:
                if ev.code == ecodes.ABS_X:
                    if abs(self.__abs_l_x - ev.value) > 2:
                        self.set_property('abs-l-x', ev.value)
                elif ev.code == ecodes.ABS_Y:
                    if abs(self.__abs_l_y - ev.value) > 2:
                        self.set_property('abs-l-y', ev.value)
                elif ev.code == ecodes.ABS_RX:
                    if abs(self.__abs_r_x - ev.value) > 2:
                        self.set_property('abs-r-x', ev.value)
                elif ev.code == ecodes.ABS_RY:
                    if abs(self.__abs_r_y - ev.value) > 2:
                        self.set_property('abs-r-y', ev.value)
            elif ev.type == events.EV_KEY:
                if ev.value == 1:
                    await self.emit('button-press-event', ev.code)
                else:
                    await self.emit('button-release-event', ev.code)

if __name__ == '__main__':
    import asyncio

    seq = 1

    def on_xy_change(controller, prop):
        global seq
        print("%s: %s: %s" % ( seq, prop.name , controller.get_property(prop.name)))
        seq += 1

    def on_btn_press(controller, btn):
        global seq
        print("%s: button-press-event: %s" % ( seq, btn))
        seq += 1

    def on_btn_release(controller, btn):
        global seq
        print("%s: button-release-event: %s" % ( seq, btn))
        seq += 1


    controller = DualShock3()
    controller.connect("notify::abs-l-x", on_xy_change)
    controller.connect("notify::abs-l-y", on_xy_change)
    controller.connect("notify::abs-r-x", on_xy_change)
    controller.connect("notify::abs-r-y", on_xy_change)

    controller.connect("button-press-event", on_btn_press)
    controller.connect("button-release-event", on_btn_release)
        
    loop = asyncio.get_event_loop()
    loop.run_until_complete(controller.dispatch())

