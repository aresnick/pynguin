def swirl(skip=2):
    nc = util.nudge_color
    c = color('rdark')
    for s in range(10, 600, skip):
        square(s, True)
        left(2)
        c = nc(c, '101%', '101%', '101%')
        color(c)
