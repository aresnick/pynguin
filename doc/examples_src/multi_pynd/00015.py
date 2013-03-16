def bugs():
    '''Create 4 pynguins at the
    corners of the screen and have
    each one follow the one at the
    next corner over.
    '''

    p = mode('pynguin')
    home()
    reap()
    clear()

    p1 = p
    p1.avatar('pynguin')
    p2 = Pynguin()
    p2.avatar('arrow')
    p3 = Pynguin()
    p3.avatar('robot')
    p4 = Pynguin()
    p4.avatar('turtle')

    xn, yn, xx, yx = viewcoords()

    p1.goto(xn, yn)
    p2.goto(xn, -yn)
    p3.goto(-xn, -yn)
    p4.goto(-xn, yn)


    def gotowards(p, pp):
        x, y = pp.xy()
        p.toward(x, y)
        p.fd(1)

    while True:
        gotowards(p1, p2)
        gotowards(p2, p3)
        gotowards(p3, p4)
        gotowards(p4, p1)
