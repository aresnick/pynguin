def sc(x):
    'x**2 + y**2 = 12**2'
    import math
    x = round(x, 5)
    if -12 <= x <= 12:
        return math.sqrt(12**2 - x**2)
    else:
        return None
