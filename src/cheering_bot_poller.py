import asyncio
import datetime
import logging
import motor.motor_asyncio
import os

from pymongo.collection import ReturnDocument

from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
log = logging.getLogger('main')

DB_USER = os.environ.get("MONGO_USER", 'root')
DB_PASS = os.environ.get("MONGO_PASS", 'rootpass')
DB_HOST = os.environ.get("MONGO_HOST", 'localhost')
TOKEN = os.environ.get("GRBOT_TOKEN", 'localhost')

DB_NAME = "grb_db"
USERS_COL_NAME = "users"

def init_mongoclient():
    conn_string=f'mongodb://{DB_USER}:{DB_PASS}@{DB_HOST}/?retryWrites=true&w=majority'
    client = motor.motor_asyncio.AsyncIOMotorClient(conn_string)
    client.admin.command('ping')
    db = client[DB_NAME]
    col = db[USERS_COL_NAME]
    return col

async def db_add_user(update: Update):
    ''' Adds record about user into mongo DB.
    '''
    result = await db.find_one_and_update(
        {'userid': update.message.chat.username, 'chatid': update.message.chat.id},
        {'$set': {
            'userid': update.message.chat.username, 
            'chatid': update.message.chat.id,
            'active': True,
            'time_added': datetime.datetime.now(datetime.UTC).replace(microsecond=0),
        }},
        projection={
            '_id': False,
            'userid' : True,
            'chatid' : True,
            'active' : True
        },
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return result

async def db_remove_user(update: Update):
    ''' Set user status in Mongo DB as active=false.
    '''
    result = await db.find_one_and_update(
        {'userid': update.message.chat.username, 'chatid': update.message.chat.id},
        {'$set': {
            'active': False,
            'time_removed': datetime.datetime.now(datetime.UTC).replace(microsecond=0),
        }},
        projection={
            '_id': False,
            'userid' : True,
            'chatid' : True,
            'active' : True
        },
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return result

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log.info(f'Received START message: [{update.message.text}] - SUBSCRIBE for user id: [{update.message.chat.username}], chat id: [{update.message.chat.id}]')
    await db_add_user(update=update)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"You subscribed for daily cheering messages from this bot")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log.info(f'Received STOP message: [{update.message.text}] - UNSUBSCRIBE for user id: [{update.message.chat.username}], chat id: [{update.message.chat.id}]')
    await db_remove_user(update=update)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"You unsubscribed for daily cheering messages from this bot")

# async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Your message: {update.message.text}')

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Sorry, I can't respond. Please use commands /start or /stop.")

def collect_os_values():
    for name, value in os.environ.items():
        print("{0}: {1}".format(name, value))

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    global db
    db = init_mongoclient()

    start_handler = CommandHandler('start', start)
    stop_handler = CommandHandler('stop', stop)
    unknown_handler_m = MessageHandler(filters.TEXT, unknown)
    # unknown_handler_c = CommandHandler(filters.COMMAND, unknown)
    # echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)

    application.add_handler(start_handler)
    application.add_handler(stop_handler)
    application.add_handler(unknown_handler_m)

    application.run_polling(poll_interval=120.0)


if __name__ == '__main__':
    # asyncio.run(main())
    # collect_os_values()
    main()