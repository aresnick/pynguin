def testcolors():
    xmin, ymin, xmax, ymax = viewcoords()

    for y in range(int(ymin), int(ymin/3)):
        color('rlight')
        goto(xmin, y)
        lineto(xmax, y)
    for y in range(int(ymin/3), int(ymax/3)):
        color('rmedium')
        goto(xmin, y)
        lineto(xmax, y)
    for y in range(int(ymax/3), int(ymax)):
        color('rdark')
        goto(xmin, y)
        lineto(xmax, y)
