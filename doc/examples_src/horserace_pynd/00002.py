def make_horses():
    names = ['pynguin', 'robot', 'arrow', 'turtle']
    horses = []
    for name in names:
        np = Pynguin()
        np.avatar(name)
        np.penup()
        horses.append(np)
    return horses
