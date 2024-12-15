from dynamicslicing.utils import remove_lines

code = """def slice_me():
    x = 5
    print("Hello World")
    if x < 10:
        x += 5
    y = 0
    return y

slice_me()
"""

lines_to_keep = [1, 2, 4, 5, 9]

reduced_code = remove_lines(code, lines_to_keep)

print(reduced_code)