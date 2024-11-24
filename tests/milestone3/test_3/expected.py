def slice_me():
    middle_age = ages[2] # slicing criterion
    new_highest_age = middle_age + highest_age
    if new_highest_age <= 150:
        ages.append(new_highest_age)
    return ages 

slice_me()