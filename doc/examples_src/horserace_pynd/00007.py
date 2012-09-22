def race(horses):
    import random
    xmin, ymin, xmax, ymax = viewcoords()
    while all_less([horse.x for horse in horses], xmax-50):
        h = random.choice(horses)
        h.forward(1)
