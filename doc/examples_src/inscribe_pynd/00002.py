def axes():
    xmin, ymin, xmax, ymax = viewcoords()

    color('white')
    width(2)

    goto(0, ymin)
    lineto(0, ymax)
    goto(20, ymin+10)
    turnto(0)
    write('y')

    goto(xmin, 0)
    lineto(xmax, 0)
    goto(xmax-40, -40)
    turnto(0)
    write('x')
