class Robot(Pynguin):
    def __init__(self):
        Pynguin.__init__(self)
        self.avatar('robot')

    def touch_all(self):
        for pyn in pynguins:
            x, y = pyn.xy()
            self.lineto(x, y)
