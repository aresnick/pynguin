def ncl(step=50):
    xmin, ymin, xmax, ymax = viewcoords()
    for x in range(int(xmin), int(xmax), step):
        goto(x, 0)
        nudge_circles()
