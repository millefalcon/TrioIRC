import trio

from irc import IRCBase

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

async def test_join_channel():
    join_happened = False
    class IRCClient(IRCBase):
        nickname = 'triobot'
        def __init__(self, host, port, chan):
            super().__init__(host, port, chan)

        async def irc_JOIN(self, prefix, params):
            global join_happened
            join_happaned = True
            print('****', prefix, params)
            self.logger.info(f"**{prefix}, {params}")
            1/0
            print('****', "nothing happened")
            assert prefix == "[JOIN]"
            raise KeyboardInterrupt

    host, port = ('irc.freenode.net', 6667)
    client = IRCClient(host, port, '#dummychannel')
    with trio.move_on_after(60):
        await client.connect()
        print("join ?", join_happened)
        if join_happened:
            assert True
