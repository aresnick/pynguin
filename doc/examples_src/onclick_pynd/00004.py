class P2(Pynguin):
    def onclick(self, x, y):
        # only change x-coord
        yo = self.y
        self.goto(x, yo)
