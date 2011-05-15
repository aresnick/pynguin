def grid(scale=20):
    xmin, ymin, xmax, ymax = viewcoords()

    color('darkGray')
    width(1)

    for x in range(scale, int(xmax), scale):
        goto(x, ymin)
        lineto(x, ymax)
        goto(-x, ymin)
        lineto(-x, ymax)

    for y in range(scale, int(ymax), scale):
        goto(xmin, y)
        lineto(xmax, y)
        goto(xmin, -y)
        lineto(xmax, -y)
