def draw_finish():
    xmin, ymin, xmax, ymax = viewcoords()
    x, y = xy()
    while y > ymin:
        fill(color='white')
        square(20)
        square(-20)
        fd(20)
        fill(color='black')
        square(20)
        square(-20)
        fd(20)
        x, y = xy()
