def eq4(x):
    '4 y**2 + x**2 / 2 = 100'
    import math
    try:
        return math.sqrt((100 - .5*x*x)/2)
    except:
        return None
