import logging
import asyncio

logger = logging.getLogger(__name__)


class HUT2(asyncio.DatagramProtocol):
    """ANEL HUT2 Driver
    """
    def __init__(self, loop, user=b"admin", password=b"anel"):
        self.loop = loop
        self.user = user
        self.password = password
        self.transport = None
        self._read = asyncio.Queue(loop=loop)

    @classmethod
    async def connect(cls, host, port=7500, local_addr=("10.0.16.10", 7700),
                      loop=None, **kwargs):
        """Connect to a Newfocus/Newport 8742 controller over Ethernet/TCP.

        Args:
            host (str): Hostname or IP address of the target device.

        Returns:
            NewFocus8742: Driver instance.
        """
        if loop is None:
            loop = asyncio.get_event_loop()
        transport, protocol = await loop.create_datagram_endpoint(
                lambda: cls(loop=loop, **kwargs), remote_addr=(host, port),
                local_addr=local_addr)
        return protocol

    def connection_made(self, transport):
        self.transport = transport
        logger.debug("connected %s", transport.get_extra_info("peername"))

    def connection_lost(self, exc):
        self.transport = None
        if exc is None:
            logger.debug("connection closed")
        else:
            logger.warning("connection lost %s", exc)

    def datagram_received(self, data, addr):
        logger.debug("received %s from %s", data, addr)
        if self._read.empty():
            logger.warning("unexpected data, ignoring")
        else:
            self._read.put_nowait((data, addr))

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.abort()

    def abort(self):
        if self.transport is not None:
            self.transport.abort()

    def do(self, cmd):
        logger.debug("do %s", cmd)
        self.transport.sendto(cmd)

    def ask(self, cmd):
        self.do(cmd)
        return self._read.get()

    def sw(self, switches):
        self.do(b"".join((
            b"Sw", switches.to_bytes(1, "big"), self.user, self.password)))
