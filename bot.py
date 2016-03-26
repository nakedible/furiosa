#!/usr/bin/python3

import asyncio, json, os

import irc3
from irc3.plugins.cron import cron

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
        for i in self.activeset: print(i)
        
    @cron('* * * * *')
    @asyncio.coroutine
    def updatescores(self):
        names = yield from self.bot.async.names('#porno3003')
        for n in names['names']: self.update_penalties_for(n, self.activeset, self.penalties)
        self.activeset = set()
        print(names)
        print("hello")
        print(self.penalties)

    def update_penalties_for(self, name, active_nicks, nick_penalties):
        if name in active_nicks: nick_penalties[name] = 0
        else: nick_penalties[name] = nick_penalties.get(name, 0) + 1

def main():
    config = dict(
        nick='furiosaxx', autojoins=['#porno3003'],
        host='localhost', port=6667, ssl=False,
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
