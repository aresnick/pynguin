def stage(l, f, depth=0, rems=None):
    x, y, h = xyh()
    pp = Pynguin()
    pp.goto(x, y)
    pp.turnto(h)

    if rems is None:
        nrems = f(float(l), pp)

    else:
        nrems = []
        for x,y,h in rems:
            pp.goto(x, y)
            pp.turnto(h)
            #pp.color(x%255,y%255,h%255)
            nrems.extend(f(float(l), pp))

    if depth:
        pp.remove()
        stage(float(l)/3, f, depth-1, nrems)
    else:
        reap()
