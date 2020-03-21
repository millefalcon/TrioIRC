import logging
import attr
import trio

from typing import Tuple, List

@attr.s(auto_attribs=True, slots=True)
class Event:
    type: str = ""
    prefix: str = ""
    params: List = []


def parsemsg(s: str) -> Tuple[str, str, List]:
    """
    Breaks a message from an IRC server into its prefix, command, and
    arguments.
    """
    prefix = ''
    trailing = []
    if not s:
        raise IRCBadMessage("Empty line.")
    if s[0:1] == ':':
        prefix, s = s[1:].split(' ', 1)
    if s.find(' :') != -1:
        s, trailing = s.split(' :', 1)
        args = s.split()
        args.append(trailing)
    else:
        args = s.split()
    command = args.pop(0)
    return prefix, command, args


CR = chr(0o15)
class IRCBase:
    nickname = 'tribot'
    def __init__(self, host, port, chan='#dummychan'):
        self.host = host
        self.port = port
        self.chan = chan
        self.logger = logging.getLogger(__file__)


    async def connect(self):
        stream = await trio.open_tcp_stream(self.host, self.port)
        self.stream = stream
        await self._identify()

    async def _identify(self):
        await self.send_message("NICK", self.nickname)
        await self.send_message('USER', self.nickname, '-', '-', f'{self.nickname} Python IRC bot')

    def _alter_collided_nick(self, nickname):
        return nickname + '_'

    async def set_nick(self, nickname):
        self.logger.info(f"setting nick to {nickname}")
        self._attempted_nick = nickname
        await self.send_message("NICK", nickname)

    async def _join(self, channel):
        await self.send_message("JOIN", channel)

    async def send_message(self, command, *args):
        parts = [command] + list(args)
        message = ' '.join(parts) + '\r\n'
        await self.stream.send_all(message.encode('utf-8'))

    async def parse(self, data: bytes):
        data = data.decode('utf-8')
        for line in data.split('\n'):
            if not line: continue
            if len(line) <= 2:
                # This is a blank line, at best.
                continue
            if line[-1] == CR:
                line = line[:-1]
            yield parsemsg(line)
            await trio.sleep(0)

    async def read_and_parse_next_event(self, stream):
        async with stream:
            async for data in stream:
                #print("data >", data)
                async for prefix, command, params in self.parse(data):
                    if command in numeric_to_symbolic:
                        command = numeric_to_symbolic[command]
                    yield Event(command, prefix, params)

    async def events(self):
        async for event in self.read_and_parse_next_event(self.stream):
            #yield event.type, event.prefix, event.params
            yield event


symbolic_to_numeric = {
    "RPL_WELCOME": '001',
    "RPL_YOURHOST": '002',
    "RPL_CREATED": '003',
    "RPL_MYINFO": '004',
    "RPL_ISUPPORT": '005',
    "RPL_BOUNCE": '010',
    "RPL_USERHOST": '302',
    "RPL_ISON": '303',
    "RPL_AWAY": '301',
    "RPL_UNAWAY": '305',
    "RPL_NOWAWAY": '306',
    "RPL_WHOISUSER": '311',
    "RPL_WHOISSERVER": '312',
    "RPL_WHOISOPERATOR": '313',
    "RPL_WHOISIDLE": '317',
    "RPL_ENDOFWHOIS": '318',
    "RPL_WHOISCHANNELS": '319',
    "RPL_WHOWASUSER": '314',
    "RPL_ENDOFWHOWAS": '369',
    "RPL_LISTSTART": '321',
    "RPL_LIST": '322',
    "RPL_LISTEND": '323',
    "RPL_UNIQOPIS": '325',
    "RPL_CHANNELMODEIS": '324',
    "RPL_NOTOPIC": '331',
    "RPL_TOPIC": '332',
    "RPL_INVITING": '341',
    "RPL_SUMMONING": '342',
    "RPL_INVITELIST": '346',
    "RPL_ENDOFINVITELIST": '347',
    "RPL_EXCEPTLIST": '348',
    "RPL_ENDOFEXCEPTLIST": '349',
    "RPL_VERSION": '351',
    "RPL_WHOREPLY": '352',
    "RPL_ENDOFWHO": '315',
    "RPL_NAMREPLY": '353',
    "RPL_ENDOFNAMES": '366',
    "RPL_LINKS": '364',
    "RPL_ENDOFLINKS": '365',
    "RPL_BANLIST": '367',
    "RPL_ENDOFBANLIST": '368',
    "RPL_INFO": '371',
    "RPL_ENDOFINFO": '374',
    "RPL_MOTDSTART": '375',
    "RPL_MOTD": '372',
    "RPL_ENDOFMOTD": '376',
    "RPL_YOUREOPER": '381',
    "RPL_REHASHING": '382',
    "RPL_YOURESERVICE": '383',
    "RPL_TIME": '391',
    "RPL_USERSSTART": '392',
    "RPL_USERS": '393',
    "RPL_ENDOFUSERS": '394',
    "RPL_NOUSERS": '395',
    "RPL_TRACELINK": '200',
    "RPL_TRACECONNECTING": '201',
    "RPL_TRACEHANDSHAKE": '202',
    "RPL_TRACEUNKNOWN": '203',
    "RPL_TRACEOPERATOR": '204',
    "RPL_TRACEUSER": '205',
    "RPL_TRACESERVER": '206',
    "RPL_TRACESERVICE": '207',
    "RPL_TRACENEWTYPE": '208',
    "RPL_TRACECLASS": '209',
    "RPL_TRACERECONNECT": '210',
    "RPL_TRACELOG": '261',
    "RPL_TRACEEND": '262',
    "RPL_STATSLINKINFO": '211',
    "RPL_STATSCOMMANDS": '212',
    "RPL_ENDOFSTATS": '219',
    "RPL_STATSUPTIME": '242',
    "RPL_STATSOLINE": '243',
    "RPL_UMODEIS": '221',
    "RPL_SERVLIST": '234',
    "RPL_SERVLISTEND": '235',
    "RPL_LUSERCLIENT": '251',
    "RPL_LUSEROP": '252',
    "RPL_LUSERUNKNOWN": '253',
    "RPL_LUSERCHANNELS": '254',
    "RPL_LUSERME": '255',
    "RPL_ADMINME": '256',
    "RPL_ADMINLOC1": '257',
    "RPL_ADMINLOC2": '258',
    "RPL_ADMINEMAIL": '259',
    "RPL_TRYAGAIN": '263',
    "ERR_NOSUCHNICK": '401',
    "ERR_NOSUCHSERVER": '402',
    "ERR_NOSUCHCHANNEL": '403',
    "ERR_CANNOTSENDTOCHAN": '404',
    "ERR_TOOMANYCHANNELS": '405',
    "ERR_WASNOSUCHNICK": '406',
    "ERR_TOOMANYTARGETS": '407',
    "ERR_NOSUCHSERVICE": '408',
    "ERR_NOORIGIN": '409',
    "ERR_NORECIPIENT": '411',
    "ERR_NOTEXTTOSEND": '412',
    "ERR_NOTOPLEVEL": '413',
    "ERR_WILDTOPLEVEL": '414',
    "ERR_BADMASK": '415',
    "ERR_TOOMANYMATCHES": '416',
    "ERR_UNKNOWNCOMMAND": '421',
    "ERR_NOMOTD": '422',
    "ERR_NOADMININFO": '423',
    "ERR_FILEERROR": '424',
    "ERR_NONICKNAMEGIVEN": '431',
    "ERR_ERRONEUSNICKNAME": '432',
    "ERR_NICKNAMEINUSE": '433',
    "ERR_NICKCOLLISION": '436',
    "ERR_UNAVAILRESOURCE": '437',
    "ERR_USERNOTINCHANNEL": '441',
    "ERR_NOTONCHANNEL": '442',
    "ERR_USERONCHANNEL": '443',
    "ERR_NOLOGIN": '444',
    "ERR_SUMMONDISABLED": '445',
    "ERR_USERSDISABLED": '446',
    "ERR_NOTREGISTERED": '451',
    "ERR_NEEDMOREPARAMS": '461',
    "ERR_ALREADYREGISTRED": '462',
    "ERR_NOPERMFORHOST": '463',
    "ERR_PASSWDMISMATCH": '464',
    "ERR_YOUREBANNEDCREEP": '465',
    "ERR_YOUWILLBEBANNED": '466',
    "ERR_KEYSET": '467',
    "ERR_CHANNELISFULL": '471',
    "ERR_UNKNOWNMODE": '472',
    "ERR_INVITEONLYCHAN": '473',
    "ERR_BANNEDFROMCHAN": '474',
    "ERR_BADCHANNELKEY": '475',
    "ERR_BADCHANMASK": '476',
    "ERR_NOCHANMODES": '477',
    "ERR_BANLISTFULL": '478',
    "ERR_NOPRIVILEGES": '481',
    "ERR_CHANOPRIVSNEEDED": '482',
    "ERR_CANTKILLSERVER": '483',
    "ERR_RESTRICTED": '484',
    "ERR_UNIQOPPRIVSNEEDED": '485',
    "ERR_NOOPERHOST": '491',
    "ERR_NOSERVICEHOST": '492',
    "ERR_UMODEUNKNOWNFLAG": '501',
    "ERR_USERSDONTMATCH": '502',
}

numeric_to_symbolic = {}
for k, v in symbolic_to_numeric.items():
    numeric_to_symbolic[v] = k

if __name__ == '__main__':
    async def main():
        logging.basicConfig(level=logging.DEBUG)
        host, port, channel = ("irc.freenode.net", 6667, "#bash")
        irc = IRCBase(host, port)
        await irc.connect()
        await irc._join(channel)
        async for event in irc.events():
            print(event)
            if event.type == 'ERR_NICKNAMEINUSE':
                await irc.set_nick(irc.nickname + '_')
                await irc._join(channel)

    trio.run(main)
