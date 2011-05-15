def trans(r, th, scale=20):
    import math
    x = r * math.cos(th) * scale
    y = r * math.sin(th) * scale
    return x, -y
