def follow_switch(n, scramble=True):
    '''Like follow() but occasionally
    a pynguin will decide to follow a
    different pynguin.
    '''

    import random
    make(n)

    if scramble:
        agoto('random')
        acolor('random')
        aturnto('random')

    def follow_who(pyn, pyns):
        following = pyn
        while following == pyn:
            following = random.choice(pyns)
        pyn.following = following

    for pyn in pynguins:
        pyn._fspeed = 1 + random.randrange(1900)/1000.
        pyn._tspeed = 3 + random.randrange(1900)/1000.
        pyn.tocenter = False
        follow_who(pyn, pynguins)

    while 1:
        for pyn in pynguins:
            if not random.randrange(300):
                follow_who(pyn, pynguins)
                print 'switch!'

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
