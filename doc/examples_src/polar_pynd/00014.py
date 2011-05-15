def point(r, th, scale=20):
    import math
    x, y = trans(r, th, scale=20)
    goto(x, y)
    fd(1)
