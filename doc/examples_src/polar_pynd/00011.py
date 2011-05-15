def axis():
    xmin, ymin, xmax, ymax = viewcoords()
    home()
    color('white')
    lineto(xmax, 0)
    goto(xmax-80, -40)
    write('th = 0')
