def scatter(n, m):
    '''create n pynguins, move them
    to random places onscreen, then
    have them move from place to
    place at random m times each.
    '''

    for c in range(n):
        pyn = Pynguin()
        pyn.goto('random')
        pyn.color('random')

    for s in range(m):
        acmd('lineto', 'random')
