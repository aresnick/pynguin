def arc(w=150, b=50, e=500, rstep=10):
    from math import sqrt
    pen = pynguin.pen
    penup()

    fd(b)

    h = b
    while h < e:
        r = sqrt(w**2 + h**2)
        pendown()
        circle(r, True)
        penup()
        fd(rstep)
        h += rstep

    if pen:
        pendown()
