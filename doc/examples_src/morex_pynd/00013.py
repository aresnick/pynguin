def bos(r=200, n=200):
    '''Draw a ball of string of approximate
    radius r centered around the
    current position.
    '''
    import random
    c = x, y = xy()
    for i in range(n):
        a = random.randint(130,170)
        lt(a)

        d = funtil(c, r)
        if d < 5:
            toward(x, y)
            fd(1)
        fd(d)

    goto(x, y)


def funtil(c, r):
    '''Used by bos()
    return the distance the pynguin can
    move forward before being distance
    r away from point c.
    '''

    import math
    xc, yc = c
    d = 1
    while True:
        x, y = xyforward(d)
        dd = math.hypot(xc-x, yc-y)
        if dd > r:
            return d
        else:
            d += 1
