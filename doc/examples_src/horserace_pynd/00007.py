def race(horses):
    import random
    xmin, ymin, xmax, ymax = viewcoords()
    xfinish = xmax - 50
    while all(horse.x < xfinish for horse in horses):
        h = random.choice(horses)
        h.forward(1)
        h.waitforit()
