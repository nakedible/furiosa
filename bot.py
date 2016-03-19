#!/usr/bin/python3

import json

import irc3

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
        self.idlemap  = set()
        self.scoremap = {}

    @irc3.event(irc3.rfc.PRIVMSG)
    def on_privmsg(self, mask=None, data=None, event=None, target=None):
        print(mask)
        print(data)
        print(event)
        print(target)
        self.idlemap.add(mask)
        for i in self.idlemap: print(i)
        


def main():
    config = dict(
        nick='furiosaxx', autojoins=['#porno3003'],
        host='irc.elisa.fi', port=6667, ssl=False,
        includes=[
            'irc3.plugins.core',
            'irc3.plugins.command',
            'irc3.plugins.human',
            __name__,  # this register MyPlugin
        ]
    )
    bot = irc3.IrcBot.from_config(config)
    bot.run(forever=True)

if __name__ == '__main__':
    main()
