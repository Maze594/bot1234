import time
import datetime
from typing import Dict, Any, Tuple

from viberbot.api.messages.text_message import TextMessage
from viberbot.api.user_profile import UserProfile
from viberbot.api.viber_requests import ViberMessageRequest, ViberConversationStartedRequest

from src.users import UserContext
from src.words import *

GREETING_TEXT = 'Этот бот предназначен для заучивания английских слов. Для начала работы введите start или нажмите на '\
                'кнопку внизу.'

users: Dict[Any, UserContext] = {}


def start_test(user_context: UserContext, user_id, database):
    user_context.testing = True
    user_context.test_num = 0
    user_context.counter = 0
    user_context.words_ids = generate_words_ids(user_id, database)


def next_question(user_context: UserContext, database):
    user_context.test_num += 1
    q, k = get_question(user_context, database)
    return q, k


def get_question(user_context: UserContext, database):
    if user_context.test_num >= len(user_context.words_ids):
        user_context.testing = False
        q = f'Ваш результат: {(user_context.counter / len(user_context.words_ids)) * 100}%'
        k = keyboard_greetings()
    else:
        word_id = user_context.words_ids[user_context.test_num]
        word = database.get_word(word_id)
        q = question(word)
        k = keyboard(word, user_context, database)

    user_context.keyboard = k
    return q, k


def get_example(user_context: UserContext, database):
    word_id = user_context.words_ids[user_context.test_num]
    word = database.get_word(word_id)
    ex = examples(word, database)
    k = user_context.keyboard
    return ex, k


def get_greeting(user_id, db):
    user = db.get_user(None, user_id)
    right_count = db.count_right_answers(user_id, db.get_settings().right_answer_count)
    count = db.count_words()
    greet = GREETING_TEXT + f'\nКоличетсво выученных слов: {right_count}\nОставшееся количество: {count - right_count}\n'
    if user.last_answer_timestamp is not None:
        tz = datetime.timezone(datetime.timedelta(hours=3))
        dt = datetime.datetime.fromtimestamp(user.last_answer_timestamp, tz=tz)
        greet = greet + f'\nДата последнего ответа: {dt.strftime("%d.%m.%Y %H:%M:%S (+3 MSK)")}'
    k = keyboard_greetings()
    return greet, k


def check_answer(user_context: UserContext, answer: str, database):
    word_id = user_context.words_ids[user_context.test_num]
    word = database.get_word(word_id)
    return check_translation(word, answer)


def process_message(viber_request: ViberMessageRequest) -> Tuple[str, str]:
    # timestamp = viber_request.timestamp
    timestamp = int(time.time())
    message: TextMessage = viber_request.message
    user_profile: UserProfile = viber_request.sender
    text = message.text

    with Database() as database:
        user_id = database.get_user(user_profile.id)
        if user_id is None:
            database.add_user(user_profile.id)
            user_id = database.get_user(user_profile.id).id
            database.create_all_answers(user_id)
            database.commit()
        else:
            user_id = user_id.id

        if user_id not in users:
            users[user_id] = UserContext(None)

        user = users[user_id]
        if text == '__skip':
            database.update_user_last_answer_timestamp(user_id, timestamp)
        elif not user.testing:
            if text == '__begin_test':
                start_test(user, user_id, database)
                return get_question(user, database)
            else:
                return get_greeting(user_id, database)
        else:
            if text == '__show_example':
                return get_example(user, database)

            answer, *test_num = text.split('#')
            if len(test_num) == 1 and int(test_num[0]) != user.test_num:
                return None
            if check_answer(user, answer, database):
                user.counter += 1
                word_id = user.words_ids[user.test_num]
                database.update_answers_increment_count(user_id, word_id, timestamp, 1, 1)
                database.update_user_last_answer_timestamp(user_id, timestamp)
                q, k = next_question(user, database)
                s = 'Правильно!\n\n' + q
                return s, k
            else:
                word_id = user.words_ids[user.test_num]
                database.update_answers_increment_count(user_id, word_id, timestamp, 1)
                database.update_user_last_answer_timestamp(user_id, timestamp)
                q, k = next_question(user, database)
                s = 'Неправильно!\n\n' + q
                return s, k


def process_greetings(viber_request: ViberConversationStartedRequest) -> Tuple[str, str]:
    user_profile: UserProfile = viber_request.user

    with Database() as database:
        user_id = database.get_user(user_profile.id)
        if user_id is None:
            database.add_user(user_profile.id)
            user_id = database.get_user(user_profile.id).id
            database.create_all_answers(user_id)
            database.commit()
        else:
            user_id = user_id.id
        if user_id not in users:
            users[user_id] = UserContext(None)

    user = users[user_id]
    if not user.testing:
        return get_greeting(user_id, database)
    else:
        return get_question(user, database)
