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

    __step_x = 20
    __step_y = 10

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.__x = 0
        self.__y = 0

    def do_get_property(self, prop):
        if prop.name == 'x':
            return self.__x
        elif prop.name == 'y':
            return self.__y
        else:
            raise AttributeError('unknown property %s' % prop.name)

    def do_set_property(self, prop, value):
        if prop.name == 'x':
            if abs(self.__x - value) >= self.__step_x:
                self.__x = value
                self.queue_draw()
        elif prop.name == 'y':
            if abs(self.__y - value) >= self.__step_y:
                self.__y = value
                self.queue_draw()
        else:
            raise AttributeError('unknown property %s' % prop.name)

class KeyPad(XYPad):
    __gtype_name__ = 'KeyPad'

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.set_size_request(300, 300)
        self.set_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.set_property("can-focus", True)
        self.connect("key-press-event",self.on_key_press_event)
        self.connect("key-release-event",self.on_key_release_event)
        self.up = False
        self.down = False
        self.left = False
        self.right = False

    def do_draw(self, cr):
        # paint background
        bg_color = self.get_style_context().get_background_color(Gtk.StateFlags.NORMAL)
        fg_color = self.get_style_context().get_color(Gtk.StateFlags.NORMAL)

        cr.set_source_rgba(*list(bg_color))
        cr.paint()
        # draw a diagonal line
        allocation = self.get_allocation()
        padding = 5#pixels

        def cell_x(x):
            return ((allocation.width / 3) * (x - 1)) + padding
        def cell_y(y):
            return ((allocation.height / 3) * (y - 1)) + padding
        cell_w = (allocation.width / 3) - 2*padding
        cell_h = (allocation.height / 3) - 2*padding

        self.do_draw_key(cr, cell_x(2), cell_y(1), cell_w, cell_h, fg_color, bg_color, self.up)
        self.do_draw_key(cr, cell_x(2), cell_y(3), cell_w, cell_h, fg_color, bg_color, self.down)

        self.do_draw_key(cr, cell_x(1), cell_y(2), cell_w, cell_h, fg_color, bg_color, self.left)
        self.do_draw_key(cr, cell_x(3), cell_y(2), cell_w, cell_h, fg_color, bg_color, self.right)

    def do_draw_key(self, cr, x, y, w, h, fg, bg, filled=False):
        aspect = 1.0
        radius = h / 10.0
        degrees = pi / 180.0

        cr.new_sub_path()
        cr.arc (x + w - radius, y + radius, radius, -90 * degrees, 0 * degrees);
        cr.arc (x + w - radius, y + h - radius, radius, 0 * degrees, 90 * degrees);
        cr.arc (x + radius, y + h - radius, radius, 90 * degrees, 180 * degrees);
        cr.arc (x + radius, y + radius, radius, 180 * degrees, 270 * degrees);
        cr.close_path()

        cr.set_source_rgba(*list(fg));
        if filled:
            cr.stroke_preserve()
            cr.fill()
        else:
            cr.stroke()

    def on_key_press_event(self, widget, event):
        if event.keyval == Gdk.KEY_Up and self.up == False:
            self.up = True
            self.down = False
            self.set_property('y', 100)
        elif event.keyval == Gdk.KEY_Down and self.down == False:
            self.down = True
            self.up = False

            self.set_property('y', -100)
        elif event.keyval == Gdk.KEY_Left and self.left == False:
            self.left = True
            self.right = False
            self.set_property('x', -100)
        elif event.keyval == Gdk.KEY_Right and self.right == False:
            self.right = True
            self.left = False
            self.set_property('x', 100)

    def on_key_release_event(self, widget, event):
        if event.keyval == Gdk.KEY_Up and self.up == True:
            self.up = False
            self.set_property('y', 0)
        elif event.keyval == Gdk.KEY_Down and self.down == True:
            self.down = False
            self.set_property('y', 0)
        elif event.keyval == Gdk.KEY_Left and self.left == True:
            self.left = False
            self.set_property('x', 0)
        elif event.keyval == Gdk.KEY_Right and self.right == True:
            self.right = False
            self.set_property('x', 0)

class Joystick(XYPad):
    __gtype_name__ = 'Joystick'

    radius = 0.1

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.set_size_request(300, 300)
        self.set_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK)
        self.set_property("can-focus", True)
        self.connect("button-press-event",self.on_button_press_event)
        self.connect("button-release-event",self.on_button_release_event)
        self.connect("motion-notify-event",self.on_motion_notify_event)
        self.button_down = False

    def do_draw(self, cr):
        # paint background
        bg_color = self.get_style_context().get_background_color(Gtk.StateFlags.NORMAL)
        fg_color = self.get_style_context().get_color(Gtk.StateFlags.NORMAL)
        allocation = self.get_allocation()

        # Clear background
        cr.set_source_rgba(*list(bg_color))
        cr.paint()

        # scale to unit square and translate (0, 0) to be (0.5, 0.5), i.e.
        # the center of the window
        cr.scale(allocation.width, allocation.height);
        cr.translate(0.5, 0.5);
        cr.set_line_width(0.01)

        # Draw border
        degrees = 3.1415927 / 180.0
        radius = self.radius
        cr.new_sub_path()
        x = -0.5; y = -0.5; w = 1; h = 1;
        cr.arc (x + w - radius, y + radius, radius, -90 * degrees, 0 * degrees);
        cr.arc (x + w - radius, y + h - radius, radius, 0 * degrees, 90 * degrees);
        cr.arc (x + radius, y + h - radius, radius, 90 * degrees, 180 * degrees);
        cr.arc (x + radius, y + radius, radius, 180 * degrees, 270 * degrees);
        cr.close_path()
        # cr.rectangle(x,y,w,h)
        cr.set_source_rgba(*list(fg_color));
        cr.stroke()

        dot_x = self.get_property('x') * ((0.5 - radius) / 100)
        dot_y = self.get_property('y') * ((0.5 - radius) / 100) * -1

        cr.arc(dot_x, dot_y, radius, 0, 2*pi);
        cr.close_path();
        if self.button_down:
            cr.stroke_preserve()
            cr.fill()
        else:
            cr.stroke()



    def on_button_press_event(self, widget, event):
        self.button_down = True
        self.on_motion_notify_event(widget, event)

    def on_motion_notify_event(self, widget, event):
        if self.button_down:
            radius = self.radius
            w = widget.get_allocation().width
            h = widget.get_allocation().height
            x = self._convert_absolute_to_relative(event.x, w*radius, w*(1-2*radius))
            y = self._convert_absolute_to_relative(event.y, h*radius, h*(1-2*radius)) * -1

            print("D: x = %s, y = %s" % (x,y))

            self.set_property('x', x)
            self.set_property('y', y)

    def on_button_release_event(self, widget, event):
        self.button_down = False
        self.set_property('x', 0)
        self.set_property('y', 0)

    def _convert_absolute_to_relative(self,abs_val, abs_min, abs_max):
        #import pdb
        #pdb.set_trace()
        abs_val = max(abs_min, abs_val)
        abs_val = min(abs_max, abs_val)
        val_200 = ((abs_val - abs_min) / (abs_max - abs_min)) * 200
        return (val_200 - 100)

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
    app.run(sys.argv)