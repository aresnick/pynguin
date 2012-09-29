def alpha_nudge_down():
    nc = util.nudge_color
    r = 15
    c = color('random')
    fill(color=c)

    for i in range(20):
        circle(r, True)
        penup()
        fd(20)
        pendown()
        c = util.nudge_color(c, a='85%')
        color(c)
        fill(color=c)
        r += 10
