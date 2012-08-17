def follow(n, scramble=True):
    '''Create n new pynguins, each
    one following one of the others.

    Each pynguin has its own forward
    speed and turn speed randomly generated.

    If a pynguin happens to wander off the
    screen, it will head back to the center
    before resuming following its chosen
    other pynguin.

    if scramble=True all pynguins will
    be moved to random locations, turned
    to random directions, and give random
    drawing colors before starting.
    '''

    import random
    make(n)

    if scramble:
        agoto('random')
        acolor('random')
        aturnto('random')

    for n, pyn in enumerate(pynguins):
        pyn.name = 'P%s' % n
        pyn._fspeed = 1 + random.randrange(1900)/1000.
        pyn._tspeed = 3 + random.randrange(1900)/1000.
        pyn.tocenter = False
        following = pyn
        while following == pyn:
            following = random.choice(pynguins)
        pyn.following = following

    while True:
        for pyn in pynguins:
            if not pyn.onscreen():
                pyn.tocenter = True
            elif pyn.tocenter:
                x, y = pyn.xy()
                if (-20 < x < 20) and (-20 < y < 20):
                    pyn.tocenter = False

            if not pyn.tocenter:
                ang = anglefromto(pyn, pyn.following)
            else:
                ang = anglefromto(pyn)

            dang = pyn._closest_turn(ang)

            if dang > 90:
                pyn.rt(pyn._tspeed)
            elif dang > 30:
                pyn.rt(2 * pyn._tspeed / 3.)
            if dang > 0:
                pyn.rt(pyn._tspeed / 3.)
            elif dang < -90:
                pyn.lt(pyn._tspeed)
            elif dang < -30:
                pyn.lt(2 * pyn._tspeed / 3.)
            elif dang < 0:
                pyn.lt(pyn._tspeed / 3.)

            if pyn.tocenter:
                d = pyn._fspeed
            else:
                fx, fy = pyn.following.xy()
                dfxy = pyn.distance(fx, fy)
                d = min(dfxy, pyn._fspeed)

            pyn.fd(d)
