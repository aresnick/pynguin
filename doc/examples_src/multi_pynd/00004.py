def follow_switch_all(n):
    '''Like follow_switch() but
    occasionally all of the pynguins
    will decide to follow another
    pynguin.

    '''
    import random
    p._fspeed = 1
    p._tspeed = 3
    for c in range(n):
        pyn = Pynguin()
        pyn._fspeed = 1 + random.randrange(1900)/1000.
        pyn._tspeed = 3 + random.randrange(1900)/1000.

    agoto('random')
    acolor('random')
    aturnto('random')

    def follow_who(pyns):
        for p in pyns:
            following = p
            while following == p:
                following = random.choice(pyns)
            p.following = following

    for pyn in pynguins:
        pyn.tocenter = False
    follow_who(pynguins)

    while 1:
        if not random.randrange(300):
            follow_who(pynguins)
            print 'switch!'

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
