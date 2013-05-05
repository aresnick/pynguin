def fraction(n=4, d=9):
    home()
    turnto('random')
    for s in range(d):
        if s < n:
            fill()
            arc(200, 360/d, center=True, pie=True)
        else:
            nofill()
            arc(200, 360/d, center=True, pie=True)
    label(n, d)

def label(n, d):
    goto(200, -220)
    turnto(0)
    font(size=30)
    p.underline()
    n = ' %s ' % n
    write(n, align='center', valign='bottom')
    p.underline(False)
    write(d, align='center', valign='top', move=True)
    goto(-200, -220)
