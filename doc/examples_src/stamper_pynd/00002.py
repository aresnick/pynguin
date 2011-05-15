def gostamp():
    pen = p.pen
    penup()
    for line in range(10):
        while onscreen():
            fd(60)
            stamp()
        lt(10)
        bk(80)
        while onscreen():
            bk(60)
            stamp()
        rt(10)
        fd(80)
    if pen:
        pendown()
