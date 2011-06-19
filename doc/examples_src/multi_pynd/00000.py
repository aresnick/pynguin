def make(n):
    '''create n new pynguins.
    A list of all pynguins is
    always held in the pynguins
    variable.

    The examples in this file all
    use a synchronous style of
    programming. For a different
    approach, see the threaded.pyn
    example file.
    '''

    for i in range(n):
        Pynguin()
