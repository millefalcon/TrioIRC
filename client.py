import socket
import logging

from typing import Tuple, List
import trio


CR = chr(0o15)

def parsemsg(s: str) -> Tuple[str, str, List]:
    """
    Breaks a message from an IRC server into its prefix, command, and
    arguments.

    @param s: The message to break.
    @type s: L{bytes}

    @return: A tuple of (prefix, command, args).
    @rtype: L{tuple}
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
    _attempted_nick = ''
    hostname = None
    heartbeat_interval = 120
    def __init__(self, host: str=None, port: int=None, channel_name: str="#newchan"):
        self.host = host
        self.port = port
        self.channel_name = channel_name
        self.bufsize = 1024
        self.address = None
        self.logger = logging.getLogger(__file__)
        self.logger.setLevel(logging.INFO)

    async def connection_made(self):
        self.logger.info(f'connection made to {self.address}')
        if self.hostname is None:
            self.hostname = socket.getfqdn()

    async def _data_received(self, data: bytes):
        data = data.decode("utf-8")
        for line in data.split('\r\n'):
            if len(line) <= 2:
                # This is a blank line, at best.
                continue
            if line[-1] == CR:
                line = line[:-1]
            prefix, command, params = parsemsg(line)
            if command in numeric_to_symbolic:
                command = numeric_to_symbolic[command]
            await self._handle_command(command, prefix, params)

    async def _handle_command(self, command, prefix, params):
        method = getattr(self, "irc_%s" % command, None)
        #self.logger.info(f"[command] > {method} {command} {prefix} {params}")
        try:
            if method is not None:
                await method(prefix, params)
            else:
                self.irc_unknown(prefix, command, params)
        except:
            # log
            pass

    def irc_unknown(self, prefix, command, params):
        """
        Called by L{handleCommand} on a command that doesn't have a defined
        handler. Subclasses should override this method.
        """
        raise NotImplementedError(command, prefix, params)
    
    async def irc_ERR_NICKNAMEINUSE(self, prefix, params):
        """
        Called when we try to register or change to a nickname that is already
        taken.
        """
        self._attempted_nick = self.alter_collided_nick(self._attempted_nick)
        await self.set_nick(self._attempted_nick)
        await self.join(self.channel_name)

    def _alter_collided_nick(self, nickname):
        return nickname + '_'

    async def set_nick(self, nickname):
        self.logger.info(f"setting nick to {nickname}")
        self._attempted_nick = nickname
        await self.send_message("NICK", nickname)

    async def connection_lost(self):
        self.logger.info(f'connection lost from {self.address}')
        
    def _render(self, command, *args):
        """String representation of an IRC message.  DOES NOT include the
        trailing newlines.
        """
        parts = [command] + list(*args)
        # TODO assert no spaces
        # TODO assert nothing else begins with colon!
        if args and ' ' in parts[-1]:
            parts[-1] = ':' + parts[-1]
        #print(parts)
        return ' '.join(parts)

    async def send_message(self, command, *args):
        message = self._render(command, args).encode('utf-8')
        await self.socket.send(message + b'\r\n')

    async def _send_identify(self):
        await self.set_nick(self.nickname)
        await self.send_message('USER', 'trirc', '-', '-', 'trirc Python IRC bot')

    async def _join(self, channel):
        await trio.sleep(1)
        await self.send_message('JOIN', channel)

    async def _start_heartbeat(self):
        self.logger.info("sending heart beat")
        while True:
            await trio.sleep(self.heartbeat_interval)
            await self.send_message("PONG", self.hostname)

    async def connect(self) -> None:
        with trio.socket.socket() as client_sock:
            self.socket = client_sock
            #self.address = await self.socket.resolve_remote_address((self.host, self.port))
            self.address = await trio.socket.getaddrinfo(self.host, self.port)
            self.address = (self.host, self.port)
            #await self.socket.connect(self.address[0][-1])
            await self.socket.connect(self.address)
            #await self._send_identify()
            buffer = b''
            async with trio.open_nursery() as nursery:
                try:
                    nursery.start_soon(self.connection_made)
                    await self._send_identify()
                    nursery.start_soon(self._join, self.channel_name)
                    nursery.start_soon(self._start_heartbeat)
                    while True:
                        if not self.socket._sock._closed:
                            data = await self.socket.recv(self.bufsize)
                            if not data:
                                break
                            buffer += data
                            pts = buffer.split(b'\n')
                            buffer = pts.pop()
                            for el in pts:
                                nursery.start_soon(self._data_received, el)
                        else:
                            break
                    nursery.start_soon(self.connection_lost)
                except KeyboardInterrupt as interrupt:
                    print('exiting...')
                    nursery.cancel_scope.cancel()

    def run(self):
        trio.run(self.connect)


class IRCClient(IRCBase):
    nickname = 'triobot'
    async def irc_JOIN(self, prefix, params):
        self.logger.info(f"[JOIN] - {prefix} - {params}")

    async def irc_PRIVMSG(self, prefix, params):
        self.logger.info(f"[PRIVMSG] - {prefix} - {params}")

    async def irc_QUIT(self, prefix, params):
        self.logger.info(f"[QUIT]  - {prefix} - {params}")


class Client(IRCClient):
    def __init__(self, host, port, chan):
        super().__init__(host, port, chan)
        print(self.host, self.port)


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
    logging.basicConfig(level=logging.DEBUG)
    host, port = ('irc.freenode.net', 6667)
    c = Client(host, port, '#bash')
    c.run()

