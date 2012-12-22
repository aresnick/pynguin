def star(n=5, sz=100):
    if n%2:
        # odd number of sides
        angle = 180 - (360./(n*2))

    elif n%4:
        # not multiple of 4
        partang = 360./n
        goparts = (n/2)-2
        angle = goparts*partang

    else:
        # even number of sides
        partang = 360./n
        goparts = (n/2)-1
        angle = goparts*partang

    for side in range(n):
        fd(sz)
        rt(angle)
