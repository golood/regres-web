
def get_value_checkbox(value):
    if value == 'on':
        return True

    return False

def format_numbers(values):
    return list(map(lambda x: float('{:.2f}'.format(x)), values))

def format_number(value):
    return float('{:.2f}'.format(value))