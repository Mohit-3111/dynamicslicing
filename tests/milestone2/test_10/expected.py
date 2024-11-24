def slice_me():
    german_greetings = ['Hallo', 'Guten Morgen'] # slicing criterion
    translation = f"{german_greetings[0]} is {english_greetings[0]}"
    print(translation)
    # This is the translation of Hello, World!
    greeting = f"{german_greetings[0]}, Welt!"
    return greeting 

slice_me()