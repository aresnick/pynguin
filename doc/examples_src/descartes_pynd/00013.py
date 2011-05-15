def plot(eq, scale=20):
    '''eq is a function that
    accepts an x-value and
    returns a y-value.
    '''
    sign = util.sign

    xmin, ymin, xmax, ymax = viewcoords()
    xmins = xmin/scale
    xmaxs = xmax/scale
    ymins = ymin/scale - 100
    ymaxs = ymax/scale + 100
    step = float(1)/scale

    x = xmins
    y = eq(x)
    if y is not None:
        point(x, y)
        plotted = True
        signy = sign(y)
    else:
        plotted = False
        signy = 0

    for x in domain(xmins, xmaxs, step):
        yo = y
        signyo = signy
        y = eq(x)
        if y is not None and yo is not None:
            dy = abs(y - yo)
        else:
            dy = 100
        if y is None:
            continue
        if ymins < y < ymaxs:
            xs = x * scale
            ys = y * scale
            signy = sign(y)
            if plotted and (signy == signyo or dy < 2):
                lineto(xs, -ys)
            else:
                point(x, y)
                plotted = True
            signyo = signy
