# TrioIRC

A simple IRC framework using trio.

## Getting Started

```python3
from irc import IRCClient

async def main():
    async def start_heartbeat(client, interval):
        print("sending heartbeat...")
        while True:
            await trio.sleep(interval)
            await client.send_message("PONG", client.hostname)

    host, port, channel = ("irc.freenode.net", 6667, "#bash")
    client = IRCClient(host, port, channel)
    await client.connect()
    await client.join(channel)
    interval = 120
    async with trio.open_nursery() as nursery:
        nursery.start_soon(start_heartbeat, client, interval)
        async for event in client.events():
            print(event)
            if event.type == 'ERR_NICKNAMEINUSE':
                await client.handle_nicknameinuse(event.prefix, event.params)
```

### Prerequisites

`python3.6` or greater

### Installing


```
python3 -m venv .env
.env/bin/pip install -e git+https://github.com/millefalcon/TrioIRC@master#egg=trioirc
```


## Running the tests

To run tests, you need `pytest` and `pytest-trio` installed.

```
git clone https://github.com/millefalcon/TrioIRC
cd TrioIRC/
python3 -m venv .env
.env/bin/pip install pytest pytest-trio

pytest
```

## Authors

* **Han-solo** - *Initial work* - [millefalcon](https://github.com/millefalcon/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## Acknowledgments

* Thanks to [twisted](https://github.com/twisted/twisted) for getting me started in writing IRC bots and the code that parses the data.
* Thanks to [Henry](https://github.com/henry232323), whose [trioyoyo](https://github.com/henry232323/trioyoyo) implementation for inspiration.
* Thanks to [Nathaniel J. Smith] (https://github.com/njsmith) for the [trio](https://github.com/python-trio/trio), his help and insights.
