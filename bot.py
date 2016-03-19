#!/usr/bin/python3

import irc3

def main():
    config = dict(
        nick='furiosaxx', autojoins=['#porno3003'],
        host='irc.elisa.fi', port=6667, ssl=False,
        includes=[
            'irc3.plugins.core',
            'irc3.plugins.command',
            'irc3.plugins.human',
        ]
    )
    bot = irc3.IrcBot.from_config(config)
    bot.run(forever=True)

if __name__ == '__main__':
    main()
