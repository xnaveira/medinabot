import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telnetlib import Telnet
from threading import Thread
import os

admin = os.getenv('ADMIN_USER')
admin_filter = Filters.chat(username=admin)

updater = Updater(token=os.getenv('TELEGRAM_TOKEN'), use_context=True)
dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

thread_dict = {}


class GameThread(Thread):

    def __init__(self,telnet_session,context,update):
        Thread.__init__(self)
        self.telnet_session = telnet_session
        self.context = context
        self.update = update
        self.li = [b'\?\s*$', b'\>\s*$', b'\.\s*$', b'RETURN\:\s*$', b'\:\s*$']

    def run(self):
        while self.telnet_session.sock is not None:
            s = self.telnet_session.expect(self.li)
            logging.debug('The server says {}'.format(repr(s)))
            if s[1] is not None:
                if s[0] == 3: #Ends with RETURN: then hit return
                    self.telnet_session.write('\n'.encode('latin-1'))
                else:
                    self.context.bot.send_message(
                        chat_id=self.update.effective_chat.id,
                        text='```\n' + s[2].decode('latin-1').rstrip() + '\n```',
                        parse_mode='MarkDown')

    def stop(self):
        self.context.bot.send_message(
            chat_id=self.update.effective_chat.id,
            text='```\ncerrando conexión...\n```',
            parse_mode='MarkDown')
        self.telnet_session.close()

    def get_telnet_session(self):
        return self.telnet_session


def play(update, context):
    thread_dict[update.effective_chat.id] = GameThread(Telnet('medinamud.ml', 3232),context,update)
    thread_dict[update.effective_chat.id].start()


start_handler = CommandHandler('jugar', play)
dispatcher.add_handler(start_handler)

def stop(update, context):
    thread_dict[update.effective_chat.id].stop()
    del thread_dict[update.effective_chat.id]


stop_handler = CommandHandler('cerrar', stop)
dispatcher.add_handler(stop_handler)


def players(update, context):
    l = len(thread_dict)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='```\nThere are {} players online\n```'.format(l),
                             parse_mode='MarkDown')
    for key, value in thread_dict.items():
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='```\nId: {} Socket: {}\n```'.format(key,value.get_telnet_session().get_socket()),
                                 parse_mode='MarkDown')


stop_handler = CommandHandler('jugadores', players, filters=admin_filter)
dispatcher.add_handler(stop_handler)


def answer(update, context):
    tn = thread_dict[update.effective_chat.id].get_telnet_session()
    if update.message.text[0] != '/':
        if tn.sock is not None:
            answer = update.message.text + '\n'
            tn.write(answer.encode('latin-1'))
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text='```\nNo conectado al servidor, escribe /jugar para empezar o /cerrar para cerrar la sesión.\n```',
                                     parse_mode='MarkDown')


answer_handler = MessageHandler(Filters.text, answer)
dispatcher.add_handler(answer_handler)

updater.start_polling()