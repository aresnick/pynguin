def ncl(step=50):
    xmin, ymin, xmax, ymax = viewcoords()
    for x in range(xmin, xmax, step):
        goto(x, 0)
        nudge_circles()
