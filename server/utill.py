#!/usr/bin/python3
import hashlib


def get_value_checkbox(value):
    '''
    Проверяет состояние checkbox и отдает результат в булевом значении.
    :param value: состояние checkbox
    :return: состояние checkbox
    '''
    if value == 'on':
        return True

    return False

def format_numbers(values):
    '''
    Форматирует массив строк к вещественным числам.
    :param values: массив строк.
    :return: массив вещественных чисел.
    '''
    return list(map(lambda x: float('{:.2f}'.format(x)), values))

def format_number(value):
    '''
    Форматирует строку к вещественному числу.
    :param value: строка.
    :return: вещественное число.
    '''

    if value == 'Infinity':
        return value
    return float('{:.2f}'.format(float(value)))

def formatToInt(values):
    '''
    Форматирует массив строк к целым числам.
    :param values: массив строк.
    :return: массив целых чисел.
    '''

    return list(map(lambda x: int(x), values))

def appendOneForNumber(massiv):
    '''
    Прибавляет единицу ко всем элементам массива.

    :param massiv: массив целых чисел.
    :return: массив чисел.
    '''

    return list(map(lambda x: x+1, massiv))

def generateSessionId(s):
    '''
    Генератор идентификатора сессии.
    :param s: данные сессии.
    :return: хеш код сессии.
    '''

    hash_object = hashlib.md5(s.encode())

    return hash_object.hexdigest()
