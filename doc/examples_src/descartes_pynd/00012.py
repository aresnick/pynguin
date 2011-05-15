def point(x, y, scale=20):
    x = x * scale
    y = -y * scale
    goto(x, y)
    fd(1)
