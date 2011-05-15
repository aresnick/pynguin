def stampline(dist=250, skip=50):
    x = 0
    pen = p.pen
    penup()
    while x < dist:
        if not x % skip:
            stamp('arrow')
        x += 1
        fd(1)
    if pen:
        pendown()
