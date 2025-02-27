import numpy as np

from .. import cbook
try:
    from . import backend_cairo
except ImportError as e:
    raise ImportError('backend Gtk4Agg requires cairo') from e
from . import backend_agg, backend_gtk4
from .backend_cairo import cairo
from .backend_gtk4 import Gtk, _BackendGTK4
from matplotlib import transforms


class FigureCanvasGTK4Agg(backend_gtk4.FigureCanvasGTK4,
                          backend_agg.FigureCanvasAgg):
    def __init__(self, figure):
        backend_gtk4.FigureCanvasGTK4.__init__(self, figure)
        self._bbox_queue = []

    def on_draw_event(self, widget, ctx):
        allocation = self.get_allocation()
        w, h = allocation.width, allocation.height

        if not len(self._bbox_queue):
            Gtk.render_background(
                self.get_style_context(), ctx,
                allocation.x, allocation.y,
                allocation.width, allocation.height)
            bbox_queue = [transforms.Bbox([[0, 0], [w, h]])]
        else:
            bbox_queue = self._bbox_queue

        ctx = backend_cairo._to_context(ctx)

        for bbox in bbox_queue:
            x = int(bbox.x0)
            y = h - int(bbox.y1)
            width = int(bbox.x1) - int(bbox.x0)
            height = int(bbox.y1) - int(bbox.y0)

            buf = cbook._unmultiplied_rgba8888_to_premultiplied_argb32(
                np.asarray(self.copy_from_bbox(bbox)))
            image = cairo.ImageSurface.create_for_data(
                buf.ravel().data, cairo.FORMAT_ARGB32, width, height)
            ctx.set_source_surface(image, x, y)
            ctx.paint()

        if len(self._bbox_queue):
            self._bbox_queue = []

        return False

    def blit(self, bbox=None):
        # If bbox is None, blit the entire canvas to gtk. Otherwise
        # blit only the area defined by the bbox.
        if bbox is None:
            bbox = self.figure.bbox

        allocation = self.get_allocation()
        x = int(bbox.x0)
        y = allocation.height - int(bbox.y1)
        width = int(bbox.x1) - int(bbox.x0)
        height = int(bbox.y1) - int(bbox.y0)

        self._bbox_queue.append(bbox)
        self.queue_draw_area(x, y, width, height)

    def draw(self):
        backend_agg.FigureCanvasAgg.draw(self)
        super().draw()


class FigureManagerGTK4Agg(backend_gtk4.FigureManagerGTK4):
    pass


@_BackendGTK4.export
class _BackendGTK4Agg(_BackendGTK4):
    FigureCanvas = FigureCanvasGTK4Agg
    FigureManager = FigureManagerGTK4Agg
