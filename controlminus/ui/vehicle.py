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
import gi
gi.require_version("Gtk", "3.0")

from asyncio import sleep, get_event_loop, set_event_loop_policy, run_coroutine_threadsafe, create_task as spawn

import os
import bricknil

from gi.repository import GObject, Gtk, Gdk, Gio, GLib

from controlminus import GTKEventLoopPolicy
from controlminus.model import Vehicle
from controlminus.ui.widget import KeyPad, Joystick, TiltIndicator, BearingIndicator
from controlminus.ui.controller import DualShock3

class VehicleApp(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self, application_id="org.controlminus.vehicle",flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.vehicle = None
        self.vehicle_loop = None

    def do_startup(self):
        Gtk.Application.do_startup(self)

        action = Gio.SimpleAction.new("calibrate", None)
        action.connect("activate", self.on_calibrate)
        self.add_action(action)

        action = Gio.SimpleAction.new("quit", None)
        action.connect("activate", self.on_quit)
        self.add_action(action)

        self.menus = Gtk.Builder()
        self.menus.add_from_file("controlminus/ui/vehicle.menu")
        self.set_app_menu(self.menus.get_object("vehicle-menu"))


        self.builder = Gtk.Builder()
        self.builder.add_from_file("controlminus/ui/vehicle.ui")
        #keypad = KeyPad()
        keypad = Joystick()
        keypad.set_halign(Gtk.Align.CENTER)
        keypad.set_valign(Gtk.Align.CENTER)
        keypad.set_hexpand(True)
        keypad.set_vexpand(True)
        keypad.connect("notify::x", self.on_notify_x)
        keypad.connect("notify::y", self.on_notify_y)
        self.builder.get_object("keypad-box").add(keypad)

        self.bearing = BearingIndicator()
        self.bearing.set_halign(Gtk.Align.CENTER)
        self.bearing.set_valign(Gtk.Align.CENTER)
        self.bearing.set_hexpand(True)
        self.bearing.set_vexpand(True)
        self.builder.get_object("dashboard-box").add(self.bearing)

        self.pitch = TiltIndicator()
        self.pitch.set_halign(Gtk.Align.CENTER)
        self.pitch.set_valign(Gtk.Align.CENTER)
        self.pitch.set_hexpand(True)
        self.pitch.set_vexpand(True)
        self.builder.get_object("dashboard-box").add(self.pitch)

        self.roll = TiltIndicator()
        self.roll.set_halign(Gtk.Align.CENTER)
        self.roll.set_valign(Gtk.Align.CENTER)
        self.roll.set_hexpand(True)
        self.roll.set_vexpand(True)
        self.builder.get_object("dashboard-box").add(self.roll)

        telemetry = self.builder.get_object("telemetry")
        telemetry.append_column(Gtk.TreeViewColumn("Sensor", Gtk.CellRendererText(), text=0))
        telemetry.append_column(Gtk.TreeViewColumn("Value", Gtk.CellRendererText(), text=1))
        self.telemetry_store  =Gtk.TreeStore(str, str)
        telemetry.set_model(self.telemetry_store)


        controller = None
        try:
            controller = DualShock3()
            def scale(val, src, dst):
                """
                Scale the given value from the scale of src to the scale of dst.

                val: float or int
                src: tuple
                dst: tuple

                example: print(scale(99, (0.0, 99.0), (-1.0, +1.0)))
                """
                return round((float(val - src[0]) / (src[1] - src[0])) * (dst[1] - dst[0]) + dst[0])

            def x_changed(controller, prop):
                v = controller.get_property(prop.name)
                v = scale(v, (0, 255), (-100, 100))
                keypad.set_property("x", v)

            def y_changed(controller, prop):
                v = controller.get_property(prop.name)
                v = -1 * scale(v, (0, 255), (-100, 100))
                keypad.set_property("y", v)
            
            controller.connect("notify::abs-l-x", x_changed)
            controller.connect("notify::abs-r-y", y_changed)
        except:
            controller = None

        # Setup asyncio event loop:
        set_event_loop_policy(GTKEventLoopPolicy())
        self.vehicle_loop = get_event_loop()
        self.vehicle_loop.be_running()
        
        # Setup model
        self.vehicle = Vehicle()

        async def setup():
            await bricknil.init()                        
            for name, peripheral in self.vehicle.peripherals.items():
                peripheral.connect('notify', self.on_vehicle_sensor_reading_changed)
            self.on_vehicle_created()

        if controller != None:
            self.vehicle_loop.create_task(controller.dispatch())    
        self.vehicle_loop.create_task(setup())
            
        
    def do_activate(self):
        window = self.builder.get_object("app-window")
        window.set_application(self)
        window.show_all()

    def on_quit(self, widget, data):        
        async def quit():
            await bricknil.fini()
            self.quit()            
        self.vehicle_loop.create_task(quit())

    def on_calibrate(self, widget, data):
        run_coroutine_threadsafe(self.vehicle.steering_calibrate(), self.vehicle_loop)

    def on_notify_x(self, widget, prop):
        steering = widget.get_property(prop.name)
        run_coroutine_threadsafe(self.vehicle.steer(steering, 50), self.vehicle_loop)

    def on_notify_y(self, widget, prop):
        speed = widget.get_property(prop.name)
        run_coroutine_threadsafe(self.vehicle.speed(speed), self.vehicle_loop)

    def on_vehicle_sensor_reading_changed(self, peripheral):
        for cap in peripheral.capabilities:
            cap_item = self.telemetry_store_map[(peripheral, cap)]
            cap_value = peripheral.value[cap]
            self.telemetry_store[cap_item][1] = str(cap_value)
        if peripheral == self.vehicle.position:
            self.bearing.set_property("angle", peripheral.sense_pos[0])
            self.pitch.set_property("angle", peripheral.sense_pos[1])
            self.roll.set_property("angle", peripheral.sense_pos[2])

    def on_vehicle_created(self):
        self.telemetry_store_map = {}
        for name, peripheral in self.vehicle.peripherals.items():
            peripheral_item = self.telemetry_store.append(None, [name, ''])
            for cap in peripheral.capabilities:
                cap_value = peripheral.value[cap] if peripheral.value != None else 'N/A'
                cap_item = self.telemetry_store.append(peripheral_item, [ cap.name, str(cap_value) ])
                self.telemetry_store_map[(peripheral, cap)] = cap_item
