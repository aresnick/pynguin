def all_less(lst, val):
    for var in lst:
        if var > val:
            return False
    return True
