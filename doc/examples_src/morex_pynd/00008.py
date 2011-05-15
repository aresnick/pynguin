def iffercolor(n):
    colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0)]
    for c in range(n):
        goto('random')
        x, y = xy()
        if x < 0:
            if y < 0:
                c = colors[0]
                color(*c)
                fill(color=c)
                star(5, 20)
            else:
                c = colors[1]
                color(*c)
                fill(color=c)
                square(20)
        else:
            if y < 0:
                c = colors[2]
                color(*c)
                fill(color=c)
                circle(10)
            else:
                c = colors[3]
                color(*c)
                fill(color=c)
                poly(3, 20)
