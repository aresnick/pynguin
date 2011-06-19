def anglefromto(pyn1, pyn2=None):
    '''return the angle from pynguin
    pyn1 to pynguin pyn2.
    '''

    x1, y1 = pyn1.xy()
    if pyn2 is not None:
        x2, y2 = pyn2.xy()
    else:
        x2, y2 = 0, 0
    dx = x2 - x1
    dy = y2 - y1
    import math
    rad = math.atan2(dy, dx)
    ang = math.degrees(rad)
    return ang
