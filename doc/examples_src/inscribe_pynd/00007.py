def tri(eq, x1, scale=20):
    xmin, ymin, xmax, ymax = viewcoords()
    xmins = xmin/scale
    xmaxs = xmax/scale
    step = float(1)/scale

    x = xmins
    y = eq(x)
    if y is not None:
        raise ValueError, 'screen too narrow'
    x0 = None
    x2 = None
    for x in domain(xmins, xmaxs, step):
        y = eq(x)
        if x0 is None and y is not None:
            x0 = round(x, 5)
        if x0 is not None and y is not None:
            x2 = round(x, 5)

    point(x0, 0)
    y1 = eq(x1)
    if y1 is not None:
        x1s = x1 * scale
        y1s = -y1 * scale
        lineto(x1s, y1s)
    x2s = x2 * scale
    lineto(x2s, 0)

    return x0, x1, x2
