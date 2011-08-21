def testnudgecolor():
    nc = util.nudge_color
    xmin, ymin, xmax, ymax = viewcoords()

    c = color('rmedium')
    for y in range(ymin, ymin/3):
        goto(xmin, y)
        lineto(xmax, y)
        c = nc(c, r=.4)
        color(c)
    for y in range(ymin/3, ymax/3):
        goto(xmin, y)
        lineto(xmax, y)
        c = nc(c, b=-1.4)
        color(c)
    for y in range(ymax/3, ymax):
        goto(xmin, y)
        lineto(xmax, y)
        c = nc(c, g='99.3%', b=0.3)
        color(c)
