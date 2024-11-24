def slice_me():
    highest_age = ages[-1] # slicing criterion
    new_highest_age = middle_age + highest_age
    ages.append(new_highest_age)
    for age in ages:
        if age == 150:
            print("Bye!")
    return ages

slice_me()