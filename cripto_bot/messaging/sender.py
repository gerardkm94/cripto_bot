#!/usr/bin/env python
# pylint: disable=W0613, C0116
# type: ignore[union-attr]
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to send timed Telegram messages.
This Bot uses the Updater class to handle the bot and the JobQueue to send
timed messages.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Alarm Bot example, sends a message after a set time.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

from telegram.ext import Updater, CommandHandler, CallbackContext, Handler
from telegram import Update, message, update
import logging
from os import stat, stat_result
import json
from typing import Text
import threading
import time
from cripto_bot.operations.pooler import CoinMarketApi
from cripto_bot.messaging.messages import messages

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


class TelegramSender():
    """ Class to define a Telegram sender with its own set functions """

    def __init__(self) -> None:
        self.updater = Updater(
            "1699228037:AAGU-zLIj4w2o30CEHb4pFe68WDIx6YBhaQ")
        self.dispatcher = self.updater.dispatcher
        self.clients = {}

    def set_values(self, value_list, chat_id):
        """ Set received values for criptos dict"""
        coin, value, action = value_list
        self.clients[chat_id][0].criptos[coin] = []
        self.clients[chat_id][0].criptos[coin].append(float(value))
        self.clients[chat_id][0].criptos[coin].append(action)

        if coin not in self.clients[chat_id][0].pairs:
            self.clients[chat_id][0].pairs.append(coin)

    def server_status(self, update: Update, context: CallbackContext) -> None:
        update.message.reply_text("El servidor está operativo")

    def stop_notifications(self, update: Update, context: CallbackContext) -> None:
        chat_id = update.message.chat_id
        self.clients[chat_id][1] = False
        update.message.reply_text(messages.get('disable_notifications'))

    def enable_notifications(self, update: Update, context: CallbackContext) -> None:
        chat_id = update.message.chat_id
        self.clients[chat_id][1] = True
        update.message.reply_text(messages.get('enable_notifications'))

    def join(self, update: Update, context: CallbackContext) -> None:
        chat_id = update.message.chat_id
        self.clients[chat_id] = [CoinMarketApi(), True]

        update.message.reply_text(messages.get('join'))

    def alarm(self, context):
        """Send the alarm message."""
        job = context.job
        context.bot.send_message(job.context, text="Nuevo valor seteado!")

    def set_alarm(self, update: Update, context: CallbackContext):
        """ Set the alarm """
        chat_id = update.message.chat_id
        self.set_values(context.args, chat_id)
        context.job_queue.run_once(
            self.alarm, 1, context=chat_id, name=str(chat_id))

    def send_message(self, message, chat_id):
        self.updater.bot.send_message(
            chat_id=chat_id, text=message)

    def check_alarms(self, update: Update, context: CallbackContext):
        """ Check alarms """
        chat_id = update.message.chat_id

        if not self.clients[chat_id][0].criptos:
            update.message.reply_text(
                "Todavia no tienes alarmas, utiliza /valor para fijar alguna!")
        else:
            update.message.reply_text(json.dumps(
                self.clients[chat_id][0].criptos))

    def commands(self, update: Update, context: CallbackContext):
        chat_id = update.message.chat_id

        update.message.reply_text(messages.get('commands'))

    def check_market(self):
        """ Check if there's changes in the market"""
        while True:
            logger.info("Esperando para nueva conexion...")
            time.sleep(60)
            for client in self.clients:

                if self.clients[client][1]:

                    notifications = self.clients[client][0].get_notifications()

                    if notifications:
                        for notification in notifications:
                            self.send_message(notification, chat_id=client)

                else:
                    pass

    def init(self):
        logger.info("Iniciando servidor")

        self.dispatcher.add_handler(CommandHandler("unirme", self.join))
        self.dispatcher.add_handler(CommandHandler(
            "activar_notificaciones", self.enable_notifications))
        self.dispatcher.add_handler(CommandHandler(
            "detener_notificaciones", self.stop_notifications))
        self.dispatcher.add_handler(
            CommandHandler("valor", self.set_alarm))
        self.dispatcher.add_handler(
            CommandHandler("ver_alarmas", self.check_alarms))
        self.dispatcher.add_handler(
            CommandHandler("ver_comandos", self.commands))

        logger.info("Funciones seteadas")
        notificator = threading.Thread(target=self.check_market)
        notificator.start()
        logger.info("Cripto pooler activo")
        self.updater.start_polling()
        logger.info("Servidor operativo")
        self.updater.idle()
