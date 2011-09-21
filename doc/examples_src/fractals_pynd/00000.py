def mandelbrot(s=150):
    xmin, ymin, xmax, ymax = viewcoords()
    for x in range(xmin, xmax):
        xs = float(x)/s
        for y in range(ymin, ymax):
            ys = float(y)/s
            i = inMandelbrot(xs, ys)
            if i > 0:
                point(x, y)
