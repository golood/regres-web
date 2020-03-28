
def get_value_checkbox(value):
    if value == 'on':
        return True

    return False

def format_numbers(values):
    return list(map(lambda x: float('{:.2f}'.format(x)), values))

def format_number(value):
    if value == 'Infinity':
        return value
    return float('{:.2f}'.format(value))

def appendOneForNumber(massiv):
    '''
    Прибавляет единицу ко всем элементам массива.

    :param massiv: массив целых чисел.
    :return: массив чисел.
    '''
    return list(map(lambda x: x+1, massiv))