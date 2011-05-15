def burst(n, center=True):
    make(n)
    if center:
        x, y = 0, 0
    else:
        goto('random')
        x, y = xy()
    trun('color', 'random')
    tgoto('random')
    trun('toward', x, y)

    while 1:
        tfd(10)
        for pp in pynguins:
            if not pp.onscreen():
                pp.goto('random')
                pp.toward(x, y)
