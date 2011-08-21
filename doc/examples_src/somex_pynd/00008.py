def swirl(skip=2):
    nc = util.nudge_color
    c = color('rdark')
    for s in range(10, 600, skip):
        square(s, True)
        left(2)
        c = nc(c, r='101%', g='101%', b='101%')
        color(c)
