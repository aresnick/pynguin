def inMandelbrot(x, y, n=20):
    '''takes x and y values and treats
    them as the real and imaginary parts
    of a complex number and an integer n.

    return True if the complex number c is in
    the Mandelbrot set and False otherwise.
    '''

    c = complex(x, y)
    z = 0
    while n > 0:
        z = z**2 + c
        if abs(z) >= 2:
            return -n
        n -= 1
    return True
