def twolineside(l, pp):
    xyh = pp.xyh
    fd = pp.fd
    lt = pp.lt
    rt = pp.rt

    rems = [xyh()]
    fd(l/3)
    lt(90)
    rems.append(xyh())
    fd(l/3)
    rt(180)
    rems.append(xyh())
    fd(l/3)
    lt(90)
    rems.append(xyh())
    fd(l/3)
    lt(90)
    rems.append(xyh())
    fd(l/3)
    rt(180)
    rems.append(xyh())
    fd(l/3)
    lt(90)
    rems.append(xyh())
    fd(l/3)
    return rems
