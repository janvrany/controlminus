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
gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import GObject, Gtk, Gdk
from math import pi

def sgn(value):
    """
    Sign function
    """
    if value < 0:
        return -1
    elif value == 0:
        return 0
    else:
        return 1

def deg2rad(value):
    """
    Convert value in degrees to radians (as required used cairo)
    """
    return value * (pi / 180.0)

class XYPad(Gtk.Misc):
    __gtype_name__ = 'XYPad'

    __gproperties__ = {
        "x":   (int,  # type
            "X-value", # nick
            "X-value (in range <-100,100>) ", # blurb
            -100,  # mint
            100, # max
            0,    # default
            GObject.ParamFlags.READWRITE), # flags
        "y":   (int,  # type
            "Y-value", # nick
            "Y-value (in range <-100,100>) ", # blurb
            -100,  # min
            100, # max
            0,    # default
            GObject.ParamFlags.READWRITE), # flags
    }

    _step_x = 5
    _step_y = 5

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self._x = 0
        self._y = 0
        self.set_size_request(300, 300)
        self.set_property("can-focus", True)

    def do_get_property(self, prop):
        if prop.name == 'x':
            return self._x
        elif prop.name == 'y':
            return self._y
        else:
            raise AttributeError('unknown property %s' % prop.name)

    def set_property(self, name, value):
        if self.get_property(name) != value:
            super().set_property(name, value)

    def do_set_property(self, prop, value):
        if prop.name == 'x':
            if abs(self._x - value) > self._step_x:
                self._x = value
            self.queue_draw()
        elif prop.name == 'y':
            if abs(self._y - value) > self._step_y:
                self._y = value
            self.queue_draw()
        else:
            raise AttributeError('unknown property %s' % prop.name)

class Joystick(XYPad):
    __gtype_name__ = 'Joystick'

    radius = 0.1
    padding = 5#px

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.set_events(Gdk.EventMask.KEY_PRESS_MASK | Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK)
        self.connect("button-press-event",self.on_button_press_event)
        self.connect("button-release-event",self.on_button_release_event)
        self.connect("motion-notify-event",self.on_motion_notify_event)
        self.connect("key-press-event",self.on_key_press_event)
        self.connect("key-release-event",self.on_key_release_event)
        self._clickpoint_x = None
        self._clickpoint_y = None
        self._circle_x = 0
        self._circle_y = 0
        self._keys_pressed = []

    def do_set_property(self, prop, value):
        super().do_set_property(prop, value)
        if prop.name == 'x':
            if abs(self._circle_x - value) > self._step_x:
                self._circle_x = value
                self.queue_draw()
        elif prop.name == 'y':
            if abs(self._circle_y - value) > self._step_y:
                self._circle_y = value
                self.queue_draw()

    def do_draw(self, cr):
        # paint background
        cr.set_line_width(3)
        bg_color = self.get_style_context().get_background_color(Gtk.StateFlags.NORMAL)
        fg_color = self.get_style_context().get_color(Gtk.StateFlags.NORMAL)
        allocation = self.get_allocation()
        padding = self.padding
        radius = self.radius


        # Clear background
        cr.set_source_rgba(*list(bg_color))
        cr.paint()

        # scale to unit square and translate (0, 0) to be (0.5, 0.5), i.e.
        # the center of the window
        cr.translate(padding, padding)
        cr.scale(allocation.width - 2*padding, allocation.height - 2*padding);
        cr.set_line_width(3 / (allocation.width - 2*padding))
        cr.translate(0.5, 0.5);


        # Draw border

        cr.new_sub_path()
        x = -0.5; y = -0.5; w = 1; h = 1;
        cr.arc (x + w - radius, y + radius, radius, deg2rad(-90), deg2rad(0));
        cr.arc (x + w - radius, y + h - radius, radius, deg2rad(0), deg2rad(90));
        cr.arc (x + radius, y + h - radius, radius, deg2rad(90), deg2rad(180));
        cr.arc (x + radius, y + radius, radius, deg2rad(180), deg2rad(270));
        cr.close_path()
        # cr.rectangle(x,y,w,h)
        cr.set_source_rgba(*list(fg_color));
        cr.stroke()

        dot_x = self._circle_x * ((0.5 - radius) / 100)
        dot_y = self._circle_y * ((0.5 - radius) / 100) * -1

        cr.arc(dot_x, dot_y, radius, 0, 2*pi);
        cr.close_path();
        if self._clickpoint_x != None or len(self._keys_pressed) > 0:
            cr.stroke_preserve()
            cr.fill()
        else:
            cr.stroke()

    def on_button_press_event(self, widget, event):
        self._clickpoint_x = event.x
        self._clickpoint_y = event.y
        self.queue_draw()

    def on_button_release_event(self, widget, event):
        self._clickpoint_x = None
        self._clickpoint_y = None
        self._circle_x = 0
        self._circle_y = 0
        self.set_property('x', 0)
        self.set_property('y', 0)

    def on_motion_notify_event(self, widget, event):
        if self._clickpoint_x != None:
            radius = self.radius
            padding = self.padding
            dx = -1 * (self._clickpoint_x - event.x)
            dy = self._clickpoint_y - event.y

            w = widget.get_allocation().width - 2*padding
            h = widget.get_allocation().height - 2*padding

            x = self._convert_absolute_to_relative(dx, (w / 2) * (1 - radius))
            y = self._convert_absolute_to_relative(dy, (h / 2) * (1 - radius))

            self._circle_x = x
            self._circle_y = y
            self.queue_draw()
            if abs(self._x - x) > self._step_x:
                self.set_property('x', x)
            if abs(self._y - y) > self._step_y:
                self.set_property('y', y)

    def on_key_press_event(self, widget, event):
        if event.keyval in (Gdk.KEY_Up, Gdk.KEY_Down, Gdk.KEY_Left, Gdk.KEY_Right):
            if not event.keyval in self._keys_pressed:
                self._keys_pressed.append(event.keyval)
        if event.keyval == Gdk.KEY_Up:
            self._circle_y = 100
            self.set_property('y', 100)
        elif event.keyval == Gdk.KEY_Down:
            self._circle_y = -100
            self.set_property('y', -100)
        elif event.keyval == Gdk.KEY_Left:
            self._circle_x = -100
            self.set_property('x', -100)
        elif event.keyval == Gdk.KEY_Right:
            self._circle_x = 100
            self.set_property('x', 100)

    def on_key_release_event(self, widget, event):
        if event.keyval in (Gdk.KEY_Up, Gdk.KEY_Down, Gdk.KEY_Left, Gdk.KEY_Right):
            self._keys_pressed.remove(event.keyval)
        if event.keyval == Gdk.KEY_Up:
            self._circle_y = 0
            self.set_property('y', 0)
        elif event.keyval == Gdk.KEY_Down:
            self._circle_y = 0
            self.set_property('y', 0)
        elif event.keyval == Gdk.KEY_Left:
            self._circle_x = 0
            self.set_property('x', 0)
        elif event.keyval == Gdk.KEY_Right:
            self._circle_x = 0
            self.set_property('x', 0)

    def _convert_absolute_to_relative(self,abs_val, abs_max):
        #import pdb
        #pdb.set_trace()
        abs_val = sgn(abs_val) * min(abs(abs_max), abs(abs_val))
        rel_val = (abs_val / abs_max) * 100
        return int(rel_val)

class AngleIndicator(Gtk.Misc):
    __gtype_name__ = 'AngleIndicator'

    __gproperties__ = {
        "angle":   (int,  # type
            "Angle", # nick
            "Angle (in deg2rad, range <-0,90>) ", # blurb
            -180,  # mint
            180,   # max
            0,     # default
            GObject.ParamFlags.READWRITE), # flags
    }

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.__angle = 0

    def do_get_property(self, prop):
        if prop.name == 'angle':
            return self.__angle
        else:
            raise AttributeError('unknown property %s' % prop.name)

    def do_set_property(self, prop, value):
        if prop.name == 'angle':
            if self.__angle != value:
                self.__angle = value
                self.queue_draw()
        else:
            raise AttributeError('unknown property %s' % prop.name)

    def do_draw(self, cr):
        # paint background
        # cr.set_line_width(3)
        bg_color = self.get_style_context().get_background_color(Gtk.StateFlags.NORMAL)
        fg_color = self.get_style_context().get_color(Gtk.StateFlags.NORMAL)

        # clear background
        cr.set_source_rgba(*list(bg_color))
        cr.paint()
        cr.set_source_rgba(*list(fg_color));

        allocation = self.get_allocation()
        padding = 5#pixels

        # scale to unit square and translate (0, 0) to be (0.5, 0.5), i.e.
        # the center of the window
        cr.translate(padding, padding)
        cr.scale(allocation.width - 2*padding, allocation.height - 2*padding);
        cr.set_line_width(3 / (allocation.width - 2*padding))
        cr.translate(0.5, 0.5);

        # Draw frame (circle)
        cr.arc(0, 0, 0.5, 0, 2*pi);
        cr.close_path();
        cr.stroke()

        # Display value
        cr.set_font_size(0.3)
        label = str(abs(self.get_property("angle")))
        (x, y, width, height, dx, dy) = cr.text_extents(label)
        cr.move_to(- width / 2, height/2)
        cr.show_text(label)
        cr.stroke()

class TiltIndicator(AngleIndicator):
    __gtype_name__ = 'TiltIndicator'

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.set_size_request(75, 75)

    def do_draw(self, cr):
        super().do_draw(cr)

        # Draw visual indication
        cr.rotate(deg2rad(self.get_property("angle")))

        cr.move_to(-0.5, 0)
        cr.line_to(-0.4, 0)
        cr.stroke()

        cr.move_to(0.5, 0)
        cr.line_to(0.4, 0)
        cr.stroke()

class BearingIndicator(AngleIndicator):
    __gtype_name__ = 'BearingIndicator'

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.set_size_request(75, 75)

    def do_draw(self, cr):
        super().do_draw(cr)

        # Draw visual indication
        def do_draw_visual_indication():
            cr.move_to(-0.5, 0)
            cr.line_to(-0.4, 0)
            cr.stroke()

            cr.move_to(0.5, 0)
            cr.line_to(0.4, 0)
            cr.stroke()

            cr.move_to(0, -0.5)
            cr.line_to(0, -0.4)
            cr.stroke()

            cr.move_to(0, 0.5)
            cr.line_to(0, 0.4)
            cr.stroke()


        cr.rotate(deg2rad(self.get_property("angle")))
        do_draw_visual_indication()
        cr.move_to(0, -0.5)
        cr.line_to(0, -0.2)
        cr.stroke()
        cr.rotate(deg2rad(45))
        do_draw_visual_indication()

if __name__ == '__main__':
    import sys
    from gi.repository import Gio

    class WidgetApp(Gtk.Application):
        def __init__(self, widgetClass = KeyPad):
            Gtk.Application.__init__(self,
                                     application_id="controlminus.ui.widget",
                                     flags=Gio.ApplicationFlags.FLAGS_NONE)
            self.widgetClass = widgetClass

        def do_activate(self):
            window = Gtk.ApplicationWindow(application=self)
            widget = self.widgetClass()
            widget.connect("notify::x", self.on_notify_xy)
            widget.connect("notify::y", self.on_notify_xy)
            window.add(widget)
            window.show_all()

        def on_notify_xy(self, widget, prop):
            print("I: %s changed to %s" % ( prop.name, widget.get_property(prop.name)))

    app = WidgetApp(Joystick)
    #app = WidgetApp(TiltIndicator)
    app.run(sys.argv)