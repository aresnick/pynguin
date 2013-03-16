def tournament(n=3):
    import time

    mode('pynguin')

    winners = {}
    while not tourn_winner(winners, n):
        w = go()

        time.sleep(2)

        if w in winners:
            winners[w] += 1
        else:
            winners[w] = 1
        print(winners)

    reap()
    clear()
    penup()
    w = tourn_winner(winners, n)
    write(w)
    rt(90)
    fd(35)
    lt(90)
    write('wins!')
    bk(50)
    avatar(w)
    p.label(w)


def tourn_winner(winners, n):
    for p, wins in winners.items():
        if wins == n:
            return p

    return None
