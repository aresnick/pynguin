def plot(eq, thmax=2*PI, scale=20):
    r = eq(0)
    point(r, 0, scale)
    for th in domain(0, thmax, float(1)/scale):
        r = eq(th)
        x, y = trans(r, th, scale)
        lineto(x, y)
