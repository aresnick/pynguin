def circles():
    xmin, ymin, xmax, ymax = viewcoords()
    height = ymax - ymin
    rmax = height / 4

    r = rmax
    while r > 0:
        fill(color='random')
        circle(r)
        circle(-r)
        r -= 10
