import trio

from irc import IRCBase

from irc_v2 import IRCBase as IRCBase_V2

"""
#async def test_connect_to_irc():
#    class IRCClient(IRCBase):
#        nickname = 'triobot'
#        def __init__(self, host, port, chan):
#            super().__init__(host, port, chan)
#
#    host, port = ('irc.freenode.net', 6667)
#    client = IRCClient(host, port)
#
#    with trio.move_on_after(120):
#        trio.run(client.run)

"""

"""
#async def test_join_channel():
#    join_happened = False
#    class IRCClient(IRCBase):
#        nickname = 'triobot'
#        def __init__(self, host, port, chan):
#            super().__init__(host, port, chan)
#
#        async def irc_JOIN(self, prefix, params):
#            global join_happened
#            join_happaned = True
#            print('****', prefix, params)
#            self.logger.info(f"**{prefix}, {params}")
#            1/0
#            print('****', "nothing happened")
#            assert prefix == "[JOIN]"
#            raise KeyboardInterrupt
#
#    host, port = ('irc.freenode.net', 6667)
#    client = IRCClient(host, port, '#dummychannel')
#    with trio.move_on_after(60):
#        await client.connect()
#    assert join_happened
"""

async def test_join_channel():
    host, port, channel = ("irc.freenode.net", 6667, "#bash")
    irc = IRCBase_V2(host, port)
    await irc.connect()
    await irc._join(channel)
    async for event in irc.events():
        if event.type == 'ERR_NICKNAMEINUSE':
            await irc.set_nick(irc.nickname + '_')
            await irc._join(channel)
        if event.type == 'JOIN':
            await irc.disconnect()
            assert True
