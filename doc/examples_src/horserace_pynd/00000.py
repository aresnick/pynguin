def go():
    if mode() != 'pynguin':
        mode('pynguin')

    notrack()

    reap()
    reset()

    avatar('hidden')
    speed('instant')

    horses = setup()
    race(horses)
    return winner(horses)
