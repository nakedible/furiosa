#!/usr/bin/python3

import irc3

@irc3.plugin
class MyPlugin:
    def __init__(self, bot):
        self.bot = bot
        self.log = self.bot.log

    @irc3.event(irc3.rfc.PRIVMSG)
    def on_privmsg(self, mask=None, data=None, event=None, target=None):
        print(mask)
        print(data)
        print(event)
        print(target)

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
