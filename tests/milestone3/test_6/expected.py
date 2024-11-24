class Person:
    def __init__(self, name):
        self.name = name
            
def slice_me():
    tries_left = 3 # slicing criterion
    while (p.name in indefinite_pronouns or p.name == "Undefined") and tries_left > 0:
        print("Choose a proper name")
        tries_left -= 1

slice_me()