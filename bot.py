#!/usr/bin/python3

# TODO:
# - handle failed kicks
# - check for ops on channel?
# - track nick changes?
# - detect if not on channel?

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
BOT_KICK_LIMIT = os.environ.get('BOT_KICK_LIMIT', '100')
BOT_KICK_CRON = os.environ.get('BOT_KICK_CRON', '* * * * *')
BOT_DONT_KICK = os.environ.get('BOT_DONT_KICK', 'naked,varpushaukka')
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
        return ret.get('Item', {}).get('penalties', {})

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
    return "Olisit puhunut " + random_thing()[:100]

@irc3.plugin
class MyPlugin:
    def __init__(self, bot):
        self.bot = bot
        self.log = self.bot.log
        self.activeset = set()
        self.penalties = {}
        self.dontkick = set(BOT_DONT_KICK.lower().split(','))
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
        self.log.debug('%s %s %s %s', event, mask, target, data)
        if target == BOT_CHANNEL:
            self.activeset.add(self.canonnick(mask.nick))
            self.log.debug('added %s to activeset', self.canonnick(mask.nick))
            self.log.debug('activeset: %s', self.activeset)
        
    @cron(BOT_KICK_CRON)
    @asyncio.coroutine
    def updatescores(self):
        if self.activeset:
            self.log.info('discussion detected, listing names')
            names = yield from self.bot.async.names(BOT_CHANNEL)
            nameset = set()
            for n in names['names']: nameset.add(self.canonnick(n))
            self.log.debug('nameset: %s', nameset)
            self.log.info('updating penalties')
            self.penalties = self.storage.load_penalties()
            for n in nameset: self.update_penalties_for(n, self.activeset, self.penalties)
            self.storage.save_penalties(self.penalties)
            self.log.debug('penalties: %s', self.penalties)
            self.log.info('kicking lurkers')
            yield from self.kick_lurkers(nameset)
            self.activeset = set()
        else:
            self.log.info('all quiet on the western front')

    def canonnick(self, nickname):
        return nickname.lstrip('@+').lower()

    def update_penalties_for(self, name, active_nicks, nick_penalties):
        if name in active_nicks: nick_penalties[name] = 0
        else: nick_penalties[name] = nick_penalties.get(name, 0) + 1

    @asyncio.coroutine
    def kick_lurkers(self, nameset):
        for name in nameset:
            if self.penalties.get(name, 0) > int(BOT_KICK_LIMIT) and self.safe_kick(name):
                self.log.info('kicking %s because penalty score %d', name, self.penalties.get(name, 0))
                self.bot.kick(BOT_CHANNEL, name, random_message())
                yield from asyncio.sleep(0.2)

    def safe_kick(self, nick):
        if nick == self.bot.nick or nick in self.dontkick: return False
        return True

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
