def iffer(n):
    for c in range(n):
        goto('random')
        x, y = xy()
        if x < 0:
            if y < 0:
                star(5, 20)
            else:
                square(20)
        else:
            if y < 0:
                circle(10)
            else:
                poly(3, 20)
