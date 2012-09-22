def draw_track():
    avatar('hidden')
    xmin, ymin, xmax, ymax = viewcoords()
    startx = xmin + 40
    finishx = xmax - 40

    goto(startx, ymax-10)
    turnto(-90)
    write('start')
    lineto(startx, ymin)

    goto(finishx, ymax-10)
    turnto(-90)
    x, y = xy()
    draw_finish()
    goto(x-60, y)
    write('finish')
