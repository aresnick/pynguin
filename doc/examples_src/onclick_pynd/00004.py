class P2(Pynguin):
    def onclick(self, x, y):
        # only change x-coord
        oy = self.y
        self.goto(x, oy)
