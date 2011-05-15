def stars(n=20):
    import random
    for s in range(n):
        sz = random.randrange(10,70)
        goto('random')
        star(5,sz)
