def yinyang(radius=None, position=None, yycolor=None):
    x0, y0 = xy()
    pen = p.pen
    penup()
    color_orig = color()
    fill(color=color_orig)

    xmin, ymin, xmax, ymax = viewcoords()
    if radius is None:
        radius = (ymax - ymin) / 2.0
    diameter = 2 * radius
    if position is not None:
        x, y = position
        goto(x, y)
    if yycolor is None:
        color('random')
        yycolor = color()
        color(*color_orig)

    pendown()
    circle(radius, center=True)
    a = p.ritem.ang
    penup()
    forward(radius)
    right(90)

    import math
    d = radius * math.sin(PI*2 / 900.0)

    a0 = a
    color(*yycolor)
    fill(color=yycolor)
    pendown()
    while a < 180 + a0:
        th = ((a - a0) / 180.0) * PI / 2
        ir = 0.25 * diameter * math.sin(th) * math.sin(th) + 1
        circle(ir)
        forward(d)
        right(0.4)
        a += 0.4
    nofill()


    right(90)
    penup()
    forward(diameter / 4.0)

    pendown()
    color(*color_orig)
    fill(color=color_orig)
    circle(diameter / 20.0, center=True)

    penup()
    forward(diameter / 2.0)
    color(*yycolor)
    fill(color=yycolor)
    pendown()
    circle(diameter / 20.0, center=True)

    if not pen:
        penup()
    color(*color_orig)

    goto(x0, y0)
