def label(f):
    xmin, ymin, xmax, ymax = viewcoords()
    goto(xmin+20,ymin+20)
    turnto(0)
    color('white')
    write(f.__doc__)
