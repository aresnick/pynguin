def cfade(step=10, fade=0.1):
    import math
    nc = util.nudge_color

    xmin, ymin, xmax, ymax = viewcoords()
    goto(xmin, ymin)
    r = max(xmax-xmin, ymax-ymin)

    c = fill(color='random')
    color(c)

    # fade is the target final percentage of color
    # steps is how many nudges from beginning to end
    steps = r / step
    # n is the size of nudge that will get us to the
    # target fade in steps steps n percent nudges
    n = 100 * math.e ** (math.log(fade)/steps)
    # ns is n percent as a string
    ns = '%s%%' % n

    while r > 0:
        circle(r, True)
        r -= step
        c = nc(c, red=ns, green=ns, blue=ns)
        color(c)
        fill(color=c)
