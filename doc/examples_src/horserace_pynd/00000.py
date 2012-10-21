def go():
    mode('pynguin')

    reap()
    clear()

    horses = setup()
    race(horses)
    winner(horses)
