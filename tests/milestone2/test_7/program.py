class Person:
    def __init__(self, name):
        self.name = name
            
def slice_me():
    p = Person('Nobody') # slicing criterion
    indefinite_pronouns = ['Everybody', 'Somebody', 'Anybody']
    indefinite_pronouns.append(p.name)
    return p.name 

slice_me()