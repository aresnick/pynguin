class ZZ(Pynguin):
    def __init__(self, csize):
        Pynguin.__init__(self)
        self._csize = csize

    def cfd(self, d):
        r = self._csize / 2.0
        while d > 0:
            self.pendown()
            Pynguin.circle(self, r, True)
            self.penup()
            Pynguin.fd(self, 2*r)
            d -= 2*r

    def forward(self, d):
        self.cfd(d)
    fd = forward

    def circle(self, r):
        ox, oy = self.xy()
        oa = self.ritem.ang

        if r < 0:
            direction = 1
            r = -r
        else:
            direction = 0

        circ = 2*PI*r
        arc = self._csize
        steps = circ / arc
        angle = 360.0 / steps

        # correct for distortion
        if direction:
            self.lt(angle/2)
        else:
            self.rt(angle/2)

        for s in range(int(steps)):
            self.fd(arc)
            if direction:
                self.lt(angle)
            else:
                self.rt(angle)

        # correct for distortion
        if direction:
            self.rt(angle/2)
        else:
            self.lt(angle/2)

        self.goto(ox, oy)
        self.turnto(oa)
