def go():
    mode('pynguin')
    notrack()

    reap()
    clear()

    horses = setup()
    race(horses)
    winner(horses)
