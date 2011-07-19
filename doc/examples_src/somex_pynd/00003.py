def testcolors():
    xmin, ymin, xmax, ymax = viewcoords()

    for y in range(ymin, ymin/3):
        color('rlight')
        goto(xmin, y)
        lineto(xmax, y)
    for y in range(ymin/3, ymax/3):
        color('rmedium')
        goto(xmin, y)
        lineto(xmax, y)
    for y in range(ymax/3, ymax):
        color('rdark')
        goto(xmin, y)
        lineto(xmax, y)
