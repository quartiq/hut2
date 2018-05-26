import logging
import asyncio
from collections import namedtuple
import time

logger = logging.getLogger(__name__)


class Status(namedtuple(
    "HUT2", "time prod name ip mask gw mac port_names port_states blocked "
            "http_port io_names io_dirs io_states temp version typ power")):
    """HUT2 Status message parser and representation"""
    @classmethod
    def from_bytes(cls, data, time=None):
        """Parse status message and return a namedtuple of the fields"""
        data = data.decode("latin").strip().split(":")
        values = dict(
            time=time,
            prod=data.pop(0),
            name=data.pop(0).strip(),
            ip=data.pop(0),
            mask=data.pop(0),
            gw=data.pop(0),
            mac=data.pop(0),
            port_names=[],
            port_states=[],
            io_names=[],
            io_dirs=[],
            io_states=[]
        )
        for i in range(8):
            n, s = data.pop(0).rsplit(",", 2)
            values["port_names"].append(n)
            values["port_states"].append(int(s))
        values["blocked"] = int(data.pop(0))
        values["http_port"] = int(data.pop(0))
        for i in range(8):
            n, d, s = data.pop(0).rsplit(",", 3)
            values["io_names"].append(n)
            values["io_dirs"].append(int(d))
            values["io_states"].append(int(s))
        values["temp"] = float(data.pop(0)[:-2])
        values["version"] = data.pop(0)
        values["typ"] = data.pop(0)
        values["power"] = data
        return cls(**values)


class HUT2(asyncio.DatagramProtocol):
    """ANEL HUT2 Driver

    Power relay switch with 8 channels, and 8 channels general purpose IO.

    * Relay and IO indices start with 1.
    * Commands tend to keep the device busy for a while.
        Pace them, read back the status after a while and retry them.
    * Some commands sometimes return a status update. Since they are UDP,
        neither commands nor replies are guaranteed to arrive.

    :param user: Device user name (bytes)
    :param password: Device password (bytes)
    """
    def __init__(self, user=b"admin", password=b"anel"):
        self.user = user
        self.password = password
        self.transport = None
        self._read = []

    @classmethod
    async def connect(cls, host, port=7500,
                      local_addr=("255.255.255.255", 7700),
                      loop=None, **kwargs):
        """Connect to a Anel HUT2 via UDP

        :param host: IO or host name of the device
        :param port: UDP port on the device. Default is 7500 (unprivileged)
            as opposed to 75 (privileged). Ensure this is set correctly in the
            web interface.
        :param local_addr: Tuple of local address (or hostname) and UDP port.
            Default is ("255.255.255.255", 7500) (broadcast, unprivileged).
            The device default is to reply to port 75 (privileged).
            Ensure this is set correctly in the web interface.
        :return: HUT2 instance connected to the device
        """
        if loop is None:
            loop = asyncio.get_event_loop()
        transport, protocol = await loop.create_datagram_endpoint(
                lambda: cls(**kwargs), remote_addr=(host, port),
                local_addr=local_addr)
        return protocol

    def connection_made(self, transport):
        assert self.transport is None
        self.transport = transport
        logger.debug("connected %s", transport.get_extra_info("peername"))

    def connection_lost(self, exc):
        self.transport = None
        if exc is None:
            logger.debug("connection closed")
        else:
            logger.warning("connection lost %s", exc)

    def datagram_received(self, data, addr):
        if self.transport.get_extra_info("peername") != addr:
            logger.warning("data from unexpected source %s: %s", addr, data)
            return
        self.status = Status.from_bytes(data, time.time())
        logger.debug("status: %s", self.status)
        read = self._read[:]
        del self._read[:]
        for r in read:
            r.set_result(self.status)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        pass

    def abort(self):
        if self.transport is not None:
            self.transport.abort()

    def do(self, cmd):
        """Execute a command.

        :param cmd (bytes): Command
        """
        logger.debug("do %s", cmd)
        self.transport.sendto(cmd + b"\r\n")

    def wait(self):
        """Get a new status message.

        This returns a future.

        :return: :class:`Status` with the parsed fields
        """
        fut = asyncio.Future()
        self._read.append(fut)
        return fut

    async def get_status(self):
        """Get a status update.

        This is a coroutine.

        :return: :class:`Status` with the parsed fields
        """
        fut = self.wait()
        self.query()
        return await fut

    def query(self):
        """Query device status and settings."""
        self.do(b"wer da?")

    def sw(self, switches):
        """Set all relays.

        :param switches: Bitmask of the relay settings
        """
        self.do(b"".join((
            b"Sw", switches.to_bytes(1, "big"), self.user, self.password)))

    def sw_on(self, switch):
        """Turn a relay on

        :param switch (int): Relay index
        """
        sw = "{:d}".format(switch).encode("latin")
        self.do(b"".join((
            b"Sw_on", sw, self.user, self.password)))

    def sw_off(self, switch):
        """Turn a relay off

        :param switch (int): Relay index
        """
        sw = "{:d}".format(switch).encode("latin")
        self.do(b"".join((
            b"Sw_off", sw, self.user, self.password)))

    def st_off(self, switch, delay):
        """Turn a relay off after a delay

        :param switch (int): Relay index
        :param delay (int): Delay in seconds
        """
        sw = "{:d}".format(switch).encode("latin")
        delay = delay.to_bytes(2, "big")
        self.do(b"".join((
            b"St_off", sw, delay, self.user, self.password)))

    def io(self, ios):
        """Set all IO lines.

        :param ios (int): Bitmask of the IO state
        """
        self.do(b"".join((
            b"IO", ios.to_bytes(1, "big"), self.user, self.password)))

    def io_on(self, io):
        """Turn an IO on.

        :param io (int): IO line index
        """
        io = "{:d}".format(io).encode("latin")
        self.do(b"".join((
            b"IO_on", io, self.user, self.password)))

    def io_off(self, io):
        """Turn an IO off

        :param switch (int): IO line index
        """
        io = "{:d}".format(io).encode("latin")
        self.do(b"".join((
            b"IO_off", io, self.user, self.password)))
