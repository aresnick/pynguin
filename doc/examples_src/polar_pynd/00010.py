def grid(scale=20):
    xmin, ymin, xmax, ymax = viewcoords()
    home()
    color('darkGray')
    rmax = distance(xmin, ymin)
    for r in range(scale, int(rmax), scale):
        circle(r, True)
    for a in range(0, 360, scale):
        home()
        lt(a)
        while onscreen():
            fd(scale)
