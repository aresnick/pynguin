# monkeypatch method

p3 = Pynguin()

def p3onclick(self, x, y):
    self.goto(x, y)
    self.square(50, True)

import new
p3c = new.instancemethod(p3onclick, p3, Pynguin)
p3.onclick = p3c
