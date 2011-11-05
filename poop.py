#   Copyright 2011 David Malcolm <dmalcolm@redhat.com>
#
#   This is free software: you can redistribute it and/or modify it
#   under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful, but
#   WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see
#   <http://www.gnu.org/licenses/>.

from collections import namedtuple

# Text rendering:

def show_text_NE(ctx, text, x, y):
    #fe = ctx.font_extents()
    #ctx.set_source_rgb(0, 0, 0)
    te = ctx.text_extents(text)
    ctx.move_to(x - te[2], y - te[1])
    ctx.show_text(text)

def show_text_N(ctx, text, x, y):
    te = ctx.text_extents(text)
    ctx.move_to(x - te[2]/2, y - te[1])
    ctx.show_text(text)

def show_text_NW(ctx, text, x, y):
    #fe = ctx.font_extents()
    #print(fe)
    te = ctx.text_extents(text)
    ctx.move_to(x, y - te[1])
    ctx.show_text(text)

def show_text_S(ctx, text, x, y):
    te = ctx.text_extents(text)
    ctx.move_to(x - te[2]/2, y)
    ctx.show_text(text)

class Coord(namedtuple('Coord', ('x', 'y'))):
    pass

class Time(namedtuple('Time', ('hour', 'minute'))):
    def __str__(self):
        return '%s:%02i %s' % (self.hour12(), self.minute, self.ampm())

    def hour12(self):
        h = self.hour
        if h >= 12:
            h -= 12
        if h == 0:
            h = 12
        return h

    def ampm(self):
        if self.is_pm():
            return 'pm'
        else:
            return 'am'

    def is_pm(self):
        if self.hour < 12:
            return False
        else:
            return True

    def get_minute_within_day(self):
        return self.hour * 60 + self.minute

class Column(namedtuple('Column',
                        ('name', 'startx', 'endx', 'subcolumns'))):
    def centre_x(self):
        return (self.endx + self.startx)/2

class Layout:
    def __init__(self, size):
        self.size = size
        self.headingcolor = (0, 0, 0, 1)
        self.hourcolor = (0, 0, 0, 1)
        self.color15mins = (0, 0, 0, 0.25)
        self.color5mins = (0, 0, 0, 0.1)

        self.colheading_y = 20
        self.grid_tl = Coord(50, 40)

        colnames  = ['Feeding', 'Awake', 'Sleeping', 'Diapers', 'Notes']
        relcolwidths = (1.0, 0.5, 0.5, 2.0, 1.0)
        self.columns = []
        startx = 100
        colwidth = 100
        for i, (colname, relcolwidth) in enumerate(zip(colnames, relcolwidths)):
            width = colwidth * relcolwidth
            endx = startx + width

            if colname == 'Diapers':
                subcolumns = []
                substartx = startx
                for j, (subname, relcolwidth) in enumerate(zip(['Urine', 'Stool', 'Clean'],
                                                               [1.0, 1.0, 0.5])):
                    subwidth = width * relcolwidth / 2.5
                    subendx = substartx + subwidth
                    subcolumns.append(Column(subname,
                                             substartx,
                                             subendx,
                                             []))
                    substartx += subwidth
            else:
                subcolumns = []
            column = Column(colname, startx, endx, subcolumns)
            self.columns.append(column)
            startx += width

    def get_y_for_time(self, time):
        return self.grid_tl.y + (time.get_minute_within_day() * 0.50)

    def get_x_for_time(self):
        return self.grid_tl.x

    def get_x_for_column(self, idx):
        return 100 + (idx * 125)

    def render(self, ctx):
        layout._render_times(ctx)
        layout._render_columns(ctx, self.columns, 0)

    def _render_times(self, ctx):
        for hour in range(0, 24):
            for minute in range(0, 60, 5):
                time = Time(hour, minute)
                x = self.get_x_for_time()
                y = self.get_y_for_time(time)

                if minute == 0: # and hour == 0:
                    ctx.set_source_rgba(*self.hourcolor)
                elif minute % 15 == 0:
                    ctx.set_source_rgba(*self.color15mins)
                else:
                    ctx.set_source_rgba(*self.color5mins)

                # Draw text:
                if minute == 0:
                    # highlight the hour
                    show_text_NE(ctx, '%s:00' % time.hour12(), x, y)
                    show_text_NW(ctx, time.ampm(), x + 5, y)
                elif minute % 15 == 0:
                    # otherwise just 15 minute intervals
                    show_text_NE(ctx, str(minute), x, y)

                # Draw lines:
                ctx.set_line_width(0.1)
                ctx.move_to(5, y)
                ctx.line_to(self.size.x-5, y)
                ctx.stroke()

    def _render_columns(self, ctx, columns, depth):
        heading_y = 20 + (10 * depth)
        if columns:
            ctx.set_source_rgba(*self.headingcolor)
            ctx.set_line_width(0.1)
            ctx.move_to(columns[0].startx, heading_y)
            ctx.line_to(columns[-1].endx, heading_y)
            ctx.stroke()

        for column in columns:
            ctx.set_source_rgba(*self.headingcolor)
            show_text_N(ctx, column.name, column.centre_x(), heading_y)

            x = column.startx
            ctx.set_line_width(0.1)
            ctx.move_to(x, heading_y)
            ctx.line_to(x, self.size.y)
            ctx.stroke()

            if column.subcolumns:
                ctx.move_to(column.startx, heading_y)
                ctx.line_to(column.endx, heading_y)
                ctx.stroke()

            self._render_columns(ctx, column.subcolumns, depth + 1)

def inch_to_point(inch):
    return inch * 72.0

uslettersize_inches = Coord(8.5, 11)
uslettersize_points = Coord(*tuple(inch_to_point(inch) for inch in uslettersize_inches))
pagesize_points = uslettersize_points

# print(pagesize_points)

import cairo
surf = cairo.PDFSurface('poop.pdf',
                        pagesize_points[0],
                        pagesize_points[1])
ctx = cairo.Context(surf)

# Fill with white:
ctx.set_source_rgb(1, 1, 1)
ctx.paint()

layout = Layout(pagesize_points)
layout.render(ctx)
surf.finish()
