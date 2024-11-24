def slice_me():
    middle_age = ages[2] # slicing criterion
    new_highest_age = middle_age + highest_age
    ages.append(new_highest_age)
    return ages 

slice_me()