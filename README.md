# furiosa

IRC bot designed to kick lurkers not participating in discussions
after a certain time.

## Behavior

The bot will periodically list all users on the channel and award lurk
points for everyone not participating in discussion and resetting the
lurk points for everyone participating in discussion, if there was
discussion during that period. When a user has too many lurk points,
the bot will kick that user from the channel.

This logic should robustly track people who do not participate in
discussions, but should not get confused by the bot being offline, or
in a netsplit, or frozen, as timestamp based methods might.
