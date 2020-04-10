import copy
import json
import random

from src.database import *

with open('./english_words.json', 'r', encoding='utf-8') as f:
    all_words = json.load(f)


WORDS_PER_TEST = 4


def generate_words_ids(user_id, database):
    settings = database.get_settings()
    right_answer_count = settings.right_answer_count
    test_length = settings.test_length

    # Если пользователю осталось учить меньше слов чем TEST_LENGTH, ошибки не будет
    words = database.get_words_for_question(user_id, right_answer_count)

    random.shuffle(words)
    return [word_id.id for word_id in words][:test_length]


GREETINGS_KEYBOARD = json.loads('''
{
    "Type": "keyboard",
    "BgColor": "#FFFFFF",
    "Buttons": [{
        "Columns": 6,
        "Rows": 1,
        "ActionType": "reply",
        "ActionBody": "__begin_test",
        "Text": "Давай начнем"
    }]
}
''')

KEYBOARD_TEMPLATE = {
    "Type": "keyboard",
    "BgColor": "#FFFFFF",
    "Buttons": []
}
BUTTON_TEMPLATE = {
    "Columns": 6,
    "Rows": 1,
    "ActionType": "reply",
    "ActionBody": None,
    "Text": None
}


def offset(i: int):
    return WORDS_PER_TEST * i


def check_translation(word, trans: str) -> bool:
    return word.translation == trans


def question(word) -> str:
    return f"Как переводится с английского слово \"{word.word}\"?"


def action_body(word, num):
    return f'{word}#{num}'


def keyboard(current_word, user_context, database):
    buttons = []
    words = [w.translation for w in database.get_words_for_keyboard(current_word.id)]
    random.shuffle(words)

    button = copy.copy(BUTTON_TEMPLATE)
    button['ActionBody'] = action_body(current_word.translation, user_context.test_num)
    button['Text'] = current_word.translation
    button['Columns'] = 3
    button['Rows'] = 1
    buttons.append(button)

    for word in words[:WORDS_PER_TEST - 1]:
        button = copy.copy(BUTTON_TEMPLATE)
        button['ActionBody'] = action_body(word, user_context.test_num)
        button['Text'] = word
        button['Columns'] = 3
        button['Rows'] = 1
        buttons.append(button)

    random.shuffle(buttons)

    button = copy.copy(BUTTON_TEMPLATE)
    button['ActionBody'] = '__show_example'
    button['Text'] = 'Привести пример'
    button['Columns'] = 6
    button['Rows'] = 1
    buttons.append(button)

    k = copy.copy(KEYBOARD_TEMPLATE)
    k['Buttons'] = buttons
    return k


def keyboard_greetings():
    return GREETINGS_KEYBOARD


def examples(word, database) -> str:
    ex = database.get_examples(word.id)
    return '\n\n'.join((e.example for e in ex))
