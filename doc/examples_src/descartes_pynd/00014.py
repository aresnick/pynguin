def domain(xmin, xmax, step):
    x = xmin
    yield x
    while x < xmax:
        x += step
        yield x
