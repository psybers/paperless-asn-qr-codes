from dataclasses import dataclass, KW_ONLY
from collections.abc import Iterator
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER, A4
from reportlab.lib.units import mm, inch


# Usage:
#   label = AveryLabels.AveryLabel(5160)
#   label.open( "labels5160.pdf" )
#   label.render( RenderAddress, 30 )
#   label.close()
#
# 'render' can either pass a callable, which receives the canvas object
# (with X,Y=0,0 at the lower right) or a string "form" name of a form
# previously created with canv.beginForm().


@dataclass
class LabelInfo:
    """Class for modeling label info"""

    _: KW_ONLY
    labels_horizontal: int
    labels_vertical: int
    label_size: tuple[float, float]
    gutter_size: tuple[float, float]
    margin: tuple[float, float]
    pagesize: tuple[float, float]
    radius: float


labelInfo: dict[str, LabelInfo] = {
    "royalgreen1660": LabelInfo(
        labels_horizontal=7,
        labels_vertical=22,
        label_size=(25.4 * mm, 9.52 * mm),
        gutter_size=(2.5 * mm, 2.45 * mm),
        margin=(11.55 * mm, 8.73 * mm),
        radius=3,
        pagesize=LETTER,
    ),
    "averyL4731": LabelInfo(
        labels_horizontal=7,
        labels_vertical=27,
        label_size=(25.4 * mm, 10 * mm),
        gutter_size=(2.5 * mm, 0),
        margin=(9 * mm, 13.5 * mm),
        radius=4,
        pagesize=A4,
    ),
    # 2.6 x 1 address labels
    "avery5160": LabelInfo(
        labels_horizontal=3,
        labels_vertical=10,
        label_size=(187, 72),
        gutter_size=(11, 0),
        margin=(14, 36),
        radius=0,
        pagesize=LETTER,
    ),
    "avery5161": LabelInfo(
        labels_horizontal=2,
        labels_vertical=10,
        label_size=(288, 72),
        gutter_size=(0, 0),
        margin=(18, 36),
        radius=0,
        pagesize=LETTER,
    ),
    # 4 x 2 address labels
    "avery5163": LabelInfo(
        labels_horizontal=2,
        labels_vertical=5,
        label_size=(288, 144),
        gutter_size=(0, 0),
        margin=(18, 36),
        radius=0,
        pagesize=LETTER,
    ),
    # 1.75 x 0.5 return address labels
    "avery5167": LabelInfo(
        labels_horizontal=4,
        labels_vertical=20,
        label_size=(1.75 * inch, 0.5 * inch),
        gutter_size=(0.3 * inch, 0),
        margin=(0.3 * inch, 0.5 * inch),
        radius=0,
        pagesize=LETTER,
    ),
    # 3.5 x 2 business cards
    "avery5371": LabelInfo(
        labels_horizontal=2,
        labels_vertical=5,
        label_size=(252, 144),
        gutter_size=(0, 0),
        margin=(54, 36),
        radius=0,
        pagesize=LETTER,
    ),
}

RETURN_ADDRESS = 5167
BUSINESS_CARDS = 5371


class AveryLabel:
    def __init__(self, label, debug, **kwargs):
        data = labelInfo[label]
        self.across = data.labels_horizontal
        self.down = data.labels_vertical
        self.size = data.label_size
        self.labelsep = (
            self.size[0] + data.gutter_size[0],
            self.size[1],
        )
        self.gutter = data.gutter_size[1]
        self.margins = data.margin
        self.topDown = True
        self.debug = debug
        self.radius = data.radius
        self.pagesize = data.pagesize
        self.position = 0
        self.__dict__.update(kwargs)

    def open(self, filename):
        self.canvas = canvas.Canvas(filename, pagesize=self.pagesize)
        if self.debug:
            self.canvas.setPageCompression(0)
        self.canvas.setLineJoin(1)
        self.canvas.setLineCap(1)

    def topLeft(self, x=None, y=None):
        if x is None:
            x = self.position
        if y is None:
            if self.topDown:
                x, y = divmod(x, self.down)
            else:
                y, x = divmod(x, self.across)

        return (
            self.margins[0] + x * self.labelsep[0],
            self.pagesize[1] - self.margins[1] - y * self.gutter - (y + 1) * self.labelsep[1],
        )

    def advance(self):
        self.position += 1
        if self.position == self.across * self.down:
            self.canvas.showPage()
            self.position = 0

    def close(self):
        if self.position:
            self.canvas.showPage()
        self.canvas.save()
        self.canvas = None

    # To render, you can either create a template and tell me
    # "go draw N of these templates" or provide a callback.
    # Callback receives canvas, width, height.
    #
    # Or, pass a callable and an iterator.  We'll do one label
    # per iteration of the iterator.

    def render(self, thing, count, *args):
        assert callable(thing) or isinstance(thing, str)
        if isinstance(count, Iterator):
            return self.render_iterator(thing, count)

        canv = self.canvas
        for i in range(count):
            canv.saveState()
            canv.translate(*self.topLeft())
            if self.debug:
                canv.setLineWidth(0.25)
                canv.roundRect(0, 0, self.size[0], self.size[1], radius=self.radius)
            if callable(thing):
                thing(canv, self.size[0], self.size[1], *args)
            elif isinstance(thing, str):
                canv.doForm(thing)
            canv.restoreState()
            self.advance()

    def render_iterator(self, func, iterator):
        canv = self.canvas
        for chunk in iterator:
            canv.saveState()
            canv.translate(*self.topLeft())
            if self.debug:
                canv.setLineWidth(0.25)
                canv.roundRect(0, 0, self.size[0], self.size[1], radius=self.radius)
            func(canv, self.size[0], self.size[1], chunk)
            canv.restoreState()
            self.advance()
