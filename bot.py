#!/usr/bin/python3

import asyncio, json, os

import irc3
from irc3.plugins.cron import cron

BOT_CHANNEL = os.environ.get('BOT_CHANNEL', '#porno3003')
BOT_SERVER = os.environ.get('BOT_SERVER', 'localhost')
BOT_PORT = int(os.environ.get('BOT_PORT', '6667'))
BOT_NICK = os.environ.get('BOT_NICK', 'furiosa')
BOT_REALNAME = os.environ.get('BOT_REALNAME', 'imperator')
BOT_USERINFO = os.environ.get('BOT_USERINFO', 'Imperator Furiosa')

### storage

def read_db(filename):
    try:
        with open(filename) as f:
            return json.load(f)
    except:
        import traceback
        traceback.print_exc()
        print('failed to read db, starting with empty')
        return {}

def write_db(filename, val):
    try:
        with open(filename, 'w') as f:
            json.dump(val, f, indent=2, sort_keys=True)
            f.write('\n')
    except:
        import traceback
        traceback.print_exc()
        print('failed to write state file, ignoring error')

### bot


@irc3.plugin
class MyPlugin:
    def __init__(self, bot):
        self.bot = bot
        self.log = self.bot.log
        self.activeset = set()
        self.penalties = {}

    @irc3.event(irc3.rfc.PRIVMSG)
    def on_privmsg(self, mask=None, data=None, event=None, target=None):
        print(mask)
        print(data)
        print(event)
        print(target)
        self.activeset.add(mask.nick)
        print(self.activeset)
        
    @cron('* * * * *')
    @asyncio.coroutine
    def updatescores(self):
        if self.activeset:
            names = yield from self.bot.async.names(BOT_CHANNEL)
            for n in names['names']: self.update_penalties_for(self.canonnick(n), self.activeset, self.penalties)
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
            if self.penalties[name] > 2 and name != 'furiosa': 
                self.bot.kick(BOT_CHANNEL, name, 'moimoi')

def main():
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
