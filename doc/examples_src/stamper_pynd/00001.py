def stampcircle():
    pen = p.pen
    penup()
    for x in range(18):
        fd(80)
        stamp()
        rt(20)
    if pen:
        pendown()
