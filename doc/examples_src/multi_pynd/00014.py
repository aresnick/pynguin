def circles(n):
    '''have all pynguins move
    to random locations and make
    a small circle.
    '''
    for i in range(n):
        allgoto('random')
        allcircle(10)
