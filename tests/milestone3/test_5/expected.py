def slice_me():
    current_age = ages[0] # slicing criterion
    while current_age < ages[-1]:
        current_age += 1
    if current_age == ages[-1]:
        ages[-1] += 50    
    return ages 

slice_me()