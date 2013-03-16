def go():
    mode('pynguin')
    home()
    notrack()
    reap()
    reset()

    avatar('hidden')
    speed('instant')

    horses = setup()
    race(horses)
    return winner(horses)
