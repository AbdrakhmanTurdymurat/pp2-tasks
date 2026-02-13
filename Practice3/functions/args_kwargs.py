def add_numbers(*numbers):
    total = 0
    for n in numbers:
        total += n
    print(total)

add_numbers(1, 2, 3)


def show_info(**info):
    for key, value in info.items():
        print(key, value)

show_info(name="Alex", age=20)


def mix(a, *args):
    print(a, args)

mix(1, 2, 3, 4)


def full_data(**data):
    print(data)

full_data(city="Almaty", country="KZ")
