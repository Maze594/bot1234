import datetime
import time

from flask import Flask, Response, render_template, request, abort, make_response, redirect, url_for
from viberbot import Api
from viberbot.api import messages
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages.text_message import TextMessage
from viberbot.api.user_profile import UserProfile
from viberbot.api.viber_requests import ViberConversationStartedRequest
from viberbot.api.viber_requests import ViberMessageRequest

from src.command_processing import process_message, process_greetings
from src.search import *
from src.words import *
from src.token_set import TokenSet

app = Flask(__name__, template_folder='../templates', static_folder='../static')


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'GET':
        with Database() as database:
            s = database.get_settings()
            return render_template('settings.html',
                                   interval=s.interval,
                                   right_answer_count=s.right_answer_count,
                                   test_length=s.test_length)
    elif request.method == 'POST':
        try:
            interval = int(request.form['interval'].strip())
            interval = max(1, min(30, interval))
            right_answer_count = int(request.form['right_answer_count'].strip())
            right_answer_count = max(1, right_answer_count)
            test_length = int(request.form['test_length'].strip())
            test_length = max(1, min(20, test_length))

            with Database() as database:
                s = database.get_settings()
                s.interval = interval
                s.right_answer_count = right_answer_count
                s.test_length = test_length
        except Exception as e:
            print('/settings exception:', e)
        except:
            print('/settings unknown exception')
        return redirect(url_for('settings'))


# Viber
message_tokens = TokenSet()


@app.route('/incoming', methods=['POST'])
def incoming():
    # every viber message is signed, you can verify the signature using this method
    if not viber.verify_signature(request.get_data(), request.headers.get('X-Viber-Content-Signature')):
        return Response(status=403)

    # this library supplies a simple way to receive a request object
    viber_request = viber.parse_request(request.get_data().decode('utf8'))
    try:
        if viber_request.message_token in message_tokens:
            return Response(status=200)
        else:
            message_tokens.add(viber_request.message_token)
    except:
        pass

    if isinstance(viber_request, ViberMessageRequest):
        res = process_message(viber_request)
        if res is not None:
            text, buttons = res
            viber.send_messages(viber_request.sender.id, [
                TextMessage(text=text, keyboard=buttons)
            ])
    elif isinstance(viber_request, ViberConversationStartedRequest):
        text, buttons = process_greetings(viber_request)
        viber.send_messages(viber_request.user.id, [
            TextMessage(text=text, keyboard=buttons)
        ])
    else:
        # TODO: ответ на остальные request'ы, кроме ошибочных (ViberFailedRequest)
        pass

    return Response(status=200)


@app.route('/viber_debug', methods=['GET', 'POST'])
def viber_debug():
    if request.method == 'GET':
        return render_template('viber_debug.html')
    else:
        message = request.form['message']
        viber_request = ViberMessageRequest()
        viber_request._timestamp = time.time()
        viber_request._message = messages.TextMessage(text=message)
        viber_request._sender = UserProfile()
        viber_request._sender._id = 'viber_debug'
        text, buttons = process_message(viber_request)
        return render_template('viber_debug.html', text=text, buttons=buttons)


with open(r'./src/settings.json', 'r') as f:
    bot_conf_dict = json.load(f)

bot_configuration = BotConfiguration(
    auth_token=bot_conf_dict['auth_token'],
    name=bot_conf_dict['name'],
    avatar=bot_conf_dict['avatar']
)

viber = Api(bot_configuration)


def set_webhook(viber):
    # setting webhook
    viber.set_webhook(bot_conf_dict['webhook_host_url'])


if __name__ == '__main__':
    # scheduler = sched.scheduler(time.time, time.sleep)
    # scheduler.enter(10, 1, set_webhook, (viber,))
    # thread = threading.Thread(target=scheduler.run)
    # thread.start()
    #app.run()
    #viber.set_webhook(bot_conf_dict['webhook_host_url'])
    pass
