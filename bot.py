#!/usr/bin/python3

import asyncio, json, os, signal

import irc3
from irc3.plugins.cron import cron

import boto3

BOT_CHANNEL = os.environ.get('BOT_CHANNEL', '#porno3003')
BOT_SERVER = os.environ.get('BOT_SERVER', 'localhost')
BOT_PORT = int(os.environ.get('BOT_PORT', '6667'))
BOT_NICK = os.environ.get('BOT_NICK', 'furiosa')
BOT_REALNAME = os.environ.get('BOT_REALNAME', 'imperator')
BOT_USERINFO = os.environ.get('BOT_USERINFO', 'Imperator Furiosa')
BOT_DYNAMODB_TABLE = os.environ.get('BOT_DYNAMODB_TABLE')
BOT_STATE_FILE = os.environ.get('BOT_STATE_FILE')

### storage

class DynamoStorage(object):
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(BOT_DYNAMODB_TABLE)

    def load_penalties(self):
        ret = self.table.get_item(Key={
            'id': 'penalties'
        }, ConsistentRead=True)
        if ret is None:
            return {}
        else:
            return ret.get('penalties', {})

    def save_penalties(self, penalties):
        self.table.put_item(Item={
            'id': 'penalties',
            'penalties': penalties
        })

class FileStorage(object):
    def __init__(self):
        self.filename = BOT_STATE_FILE

    def load_penalties(self):
        try:
            with open(self.filename) as f:
                return json.load(f)
        except:
            import traceback
            traceback.print_exc()
            print('failed to read state file, returning empty')
            return {}

    def save_penalties(self, penalties):
        try:
            with open(self.filename, 'w') as f:
                json.dump(penalties, f, indent=2, sort_keys=True)
                f.write('\n')
        except:
            import traceback
            traceback.print_exc()
            print('failed to write state file, ignoring error')

class MemoryStorage(object):
    def __init__(self):
        self.penalties = {}

    def load_penalties(self):
        # XXX: should deep copy to be safe
        return self.penalties

    def save_penalties(self, penalties):
        # XXX: should deep copy to be safe
        self.penalties = penalties

### bot

from random import random, choice

def random_qualifier():
    return choice(('hyvin', 'melko', 'toisinaan', 'vastavuoroisen'))

def random_attribute():
    if random() > 0.6: return random_qualifier() + ' ' + random_attribute()
    return choice(('ihanista', 'punaisista', 'poliittisista', 'turhista'))

def random_thing():
    if random() > 0.7: return random_thing() + ' ja ' + random_thing()
    if random() > 0.6: return random_attribute() + ' ' + random_thing()
    return choice(('pupuista', 'tytöistä', 'pojista', 'kurkuista'))

def random_message():
    return "Olisit puhunut " + random_thing()

@irc3.plugin
class MyPlugin:
    def __init__(self, bot):
        self.bot = bot
        self.log = self.bot.log
        self.activeset = set()
        self.penalties = {}
        self.dontkick = set((self.bot.nick, 'varpushaukka', 'naked'))
        # XXX: reuses same handler, mucks about in internals, but we
        # just want SIGTERM to be handled too
        self.bot.loop.add_signal_handler(signal.SIGTERM, self.bot.SIGINT)
        if BOT_DYNAMODB_TABLE is not None:
            self.storage = DynamoStorage()
        elif BOT_STATE_FILE is not None:
            self.storage = FileStorage()
        else:
            self.storage = MemoryStorage()

    @irc3.event(irc3.rfc.PRIVMSG)
    def on_privmsg(self, mask=None, data=None, event=None, target=None):
        print(mask)
        print(data)
        print(event)
        print(target)
        self.activeset.add(mask.nick)
        print(self.activeset)
        print(self.bot.nick)
        
    @cron('* * * * *')
    @asyncio.coroutine
    def updatescores(self):
        if self.activeset:
            names = yield from self.bot.async.names(BOT_CHANNEL)
            self.penalties = self.storage.load_penalties()
            for n in names['names']: self.update_penalties_for(self.canonnick(n), self.activeset, self.penalties)
            self.storage.save_penalties(self.penalties)
            self.kick_lurkers()
            self.activeset = set()
            print(names)
            print(self.penalties)

    def canonnick(self, nickname):
        return nickname.lstrip('@+').lower()

    def update_penalties_for(self, name, active_nicks, nick_penalties):
        if name in active_nicks: nick_penalties[name] = 0
        else: nick_penalties[name] = nick_penalties.get(name, 0) + 1

    def kick_lurkers(self):
        for name in self.penalties:
            if self.penalties[name] > 1 and name not in self.dontkick: 
                self.bot.kick(BOT_CHANNEL, name, random_message())

def main():
    print('connecting to {}:{}'.format(BOT_SERVER, BOT_PORT))
    config = dict(
        nick=BOT_NICK, realname=BOT_REALNAME, userinfo=BOT_USERINFO,
        autojoins=[BOT_CHANNEL],
        host=BOT_SERVER, port=BOT_PORT, ssl=False,
        includes=[
            'irc3.plugins.core',
            'irc3.plugins.async',
            __name__,  # this register MyPlugin
        ]
    )
    bot = irc3.IrcBot.from_config(config)
    bot.run(forever=True)

if __name__ == '__main__':
    main()
