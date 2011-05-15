def swirl2(skip=7):
    nc = util.nudge_color
    c = color('rlight')
    fill(color=c)
    for s in range(600, 10, -skip):
        square(s, True)
        left(4)
        c = nc(c, '99%', '99%', '99%')
        color(c)
        fill(color=c)
