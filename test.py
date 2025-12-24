import pyfiglet

for font in pyfiglet.FigletFont.getFonts():
    print(font)
    result = pyfiglet.figlet_format("Welcome to the admin portal", font=font)
    print(result)
    print("\n\n\n")


# result = pyfiglet.figlet_format("Hello, World!", font="random")
# print(result)