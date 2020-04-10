from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from src.database import Database
from src.main import viber, TextMessage
import copy
import time
import datetime
import requests


sched = BlockingScheduler()

KEYBOARD_TEMPLATE = {
    "Type": "keyboard",
    "BgColor": "#FFFFFF",
    "Buttons": []
}
BUTTON_TEMPLATE = {
    "Columns": 1,
    "Rows": 2,
    "ActionType": "reply",
    "ActionBody": None,
    "Text": None
}


@sched.scheduled_job('interval', minutes=1)
def self_request():
    resp = requests.head('https://bot123412.herokuapp.com/')
    print('self_request', resp.status_code)


@sched.scheduled_job('interval', seconds=30)
def timed_job():
    buttons = []
    button = copy.copy(BUTTON_TEMPLATE)
    button['ActionBody'] = '__begin_test'
    button['Text'] = 'Давай начнем'
    button['Columns'] = 6
    button['Rows'] = 1
    buttons.append(button)
    button = copy.copy(BUTTON_TEMPLATE)
    button['ActionBody'] = '__skip'
    button['Text'] = 'Напомнить позже'
    button['Columns'] = 6
    button['Rows'] = 1
    buttons.append(button)
    k = copy.copy(KEYBOARD_TEMPLATE)
    k['Buttons'] = buttons

    timestamp = int(time.time())
    print(f'clock: {timestamp}')
    with Database() as database:
        settings = database.get_settings()
        interval_seconds = datetime.timedelta(minutes=settings.interval).seconds
        timed_job_interval = 30

        users = database.get_users_to_notify(timestamp, interval_seconds, timed_job_interval)
        print(f'count: {len(users)}')
        if users is not None:
            for user in users:
                viber.send_messages(user.viber_id, [
                    TextMessage(text='Вы давно не проходили обучение. Хотите приступить?', keyboard=k)
                ])


sched.start()
