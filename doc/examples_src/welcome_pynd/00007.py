def conch(n=22):
    maxsize = 300.
    size_per_n = maxsize / n
    turn_per_n = 360. / n
    for turn in range(n):
        square(size_per_n*turn)
        left(turn_per_n)
