def turnside(l, pp):
    xyh = pp.xyh
    fd = pp.fd
    lt = pp.lt
    rt = pp.rt

    rems = [xyh()]
    fd(l/3)
    penup()
    fd(l/6)
    lt(90)
    fd(l/6)
    rt(180)
    rems.append(xyh())
    pendown()
    fd(l/3)
    penup()
    rt(180)
    fd(l/6)
    rt(90)
    fd(l/6)
    rems.append(xyh())
    pendown()
    fd(l/3)
    return rems
