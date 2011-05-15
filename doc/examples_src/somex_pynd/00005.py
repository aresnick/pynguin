def nudge_circles():
    nc = util.nudge_color
    xmin, ymin, xmax, ymax = viewcoords()
    height = ymax - ymin
    rmax = height / 4

    r = rmax
    c = fill(color='random')
    while r > 0:
        fill(color=c)
        color(c)
        circle(r)
        circle(-r)
        r -= 10
        c = nc(c, -5, -5, -5)
