import aiocron
import asyncio
import datetime
import logging
import motor.motor_asyncio
import pymongo
import time
import os

from pymongo.collection import ReturnDocument
from pprint import pprint

from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes

from telegram import Bot

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
USERS_COL_NAME = 'users'
MESSAGES_COL_NAME = 'messages'

def init_mongoclient(collection_name: str):
    conn_string=f'mongodb://{DB_USER}:{DB_PASS}@{DB_HOST}/?retryWrites=true&w=majority'
    client = motor.motor_asyncio.AsyncIOMotorClient(conn_string)
    client.admin.command('ping')
    db = client[DB_NAME]
    col = db[collection_name]
    return col

# async def msleep(name: str):
#     pprint(f"[{datetime.datetime.now(datetime.UTC)}] This is 1 asyncio sleep from [{name}] started")
#     await asyncio.sleep(1)
#     pprint(f"[{datetime.datetime.now(datetime.UTC)}] This is 1 asyncio sleep from [{name}] completed")
#     return True

def get_ts():
    return datetime.datetime.now(datetime.UTC).replace(microsecond=0)

async def get_new_message():
    rtrv = f'''My big hello to you today at [{datetime.datetime.now(datetime.UTC).strftime('%Y-%b-%d %H:%M:%S')}]'''
    # rtrv = 'new message 3'
    return rtrv

async def add_message_to_db(msg: str):
    print('Try to insert message into DB [{msg}]')
    result = await db_msgs.insert_one({
        'time_added' : get_ts(),
        'msg_text' : msg
        # 'total_user_count_sent' : 0,
    })
    # print(f'DB response on msg insert: [{result}]')
    return result

# async def get_one_subscribed_user():
#     # ts = datetime.datetime.now(datetime.UTC).replace(microsecond=0)
#     result = await db_users.find_one_and_update(
#         {'active': True}, 
#         {'$inc': {'count': 1}, '$set': {'done': True}}
#     )
#     return result

def get_all_subscribed_users():
    result = db_users.find(
        {'active': True}
    )
    return result

async def send_message_to_user(user: dict, message: str):
    print(f"Sending message to user: [{user['userid']}] - [{user['chatid']}]")
    result = await tgbot.send_message(chat_id=user['chatid'], text=message)
    # print(f'awaited result of [send_message_to_user]: {result}')
    return result

async def sending_loop():
    '''
    Main function for sending messages to subscribed users by cron schedule
    '''
    msg = await get_new_message()
    print(f"Received message: {msg}")
    
    while True:
        try:
            response = await add_message_to_db(msg=msg)
            # print(f'Response on add msg to db: {response}')
            break
        except pymongo.errors.DuplicateKeyError:
            print(f"This message already exists: [{msg}]")
            time.sleep(1)
    
    print("Continue next step with users.")

    while True:
        # user = await get_one_subscribed_user()
        users = get_all_subscribed_users()
        async for user in users:
            # print(f'get user: {user}')
            result = await send_message_to_user(user=user, message=msg)
            # print(f'awaited result from loop: [{result}]')
            # time.sleep(1)
        else:
            # print(f'No more active users to process')
            # time.sleep(1)
            break

def collect_os_values():
    for name, value in os.environ.items():
        print("{0}: {1}".format(name, value))

async def main():
    ts = datetime.datetime.now(datetime.UTC)
    global tgbot
    tgbot = Bot(token=TOKEN)
    global db_users
    db_users = init_mongoclient(collection_name=USERS_COL_NAME)
    global db_msgs
    db_msgs = init_mongoclient(collection_name=MESSAGES_COL_NAME)
    
    # cron_min1 = aiocron.crontab('* * * * * */30', func=msleep, args=("one",), start=True)

    cron_3 = aiocron.crontab('5 */12 * * * 0,1', func=sending_loop, args=(), start=True)

    pprint(f'[{ts}] Worker was initiated')

    while True:
        await asyncio.sleep(1)



if __name__ == '__main__':
    # collect_os_values()
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
   