def slice_me():
    ages = [0, 25, 50, 75] # slicing criterion
    current_age = 0
    while current_age < ages[-1]:
        current_age += 2 
    if current_age == ages[-1]:
        ages[-1] += 50
    return ages

slice_me()