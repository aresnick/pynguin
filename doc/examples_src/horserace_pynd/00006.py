def startline(horses):
    xmin, ymin, xmax, ymax = viewcoords()
    x = xmin + 20
    y = ymin + 100
    for horse in horses:
        horse.goto(x, y)
        y += 100
