def arcnudge(w=150, b=50, e=500, rstep=10):
    from math import sqrt
    nc = util.nudge_color
    pen = pynguin.pen
    penup()

    fd(b)

    h = b
    while h < e:
        c = color()
        color(nc(c, red='93%', green='93%', blue='98%'))
        r = sqrt(w**2 + h**2)
        circle(r, True)
        fd(rstep)
        h += rstep

    if pen:
        pendown()
