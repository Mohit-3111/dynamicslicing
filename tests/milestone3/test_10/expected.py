def slice_me():
    ages = [0, 25, 50, 75] # slicing criterion
    while current_age < ages[-1]:
        current_age += 2 
    return ages

slice_me()