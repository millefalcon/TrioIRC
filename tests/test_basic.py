import trio

from irc import IRCClient


async def test_connect():
    host, port, channel = ("irc.freenode.net", 6667, "#dummychan")
    client = IRCClient(host, port, channel)
    await client.connect()
    await client.join(channel)
    async for event in client.events():
        if event.type == 'NOTICE':
            await client.disconnect()
            assert True

async def test_join_channel():
    host, port, channel = ("irc.freenode.net", 6667, "#dummychan")
    client = IRCClient(host, port, channel)
    await client.connect()
    await client.join(channel)
    async for event in client.events():
        if event.type == 'ERR_NICKNAMEINUSE':
            await client.handle_nicknameinuse(event.prefix, event.params)
        if event.type == 'JOIN':
            await client.disconnect()
            assert True
