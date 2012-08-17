def winner(horses):
    finder = sorted([(horse.x, horse) for horse in horses])
    pos, won = finder[-1]
    name = won._imageid
    goto(-100, 0)
    turnto(0)
    msg = name + ' won!'
    write(msg)
