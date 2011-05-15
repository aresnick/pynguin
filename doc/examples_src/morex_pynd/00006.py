def colorstars(n=25):
    import random
    for s in range(n):
        sz = random.randrange(10,70)
        goto('random')
        color('random')
        star(5,sz)
