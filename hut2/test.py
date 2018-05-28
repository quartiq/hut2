import asyncio
import unittest
import os

from .protocol import HUT2


target = os.getenv("HUT2")
@unittest.skipIf(not target, "HUT2 environment variable not defined")
class HUT2Test(unittest.TestCase):
    def with_device(self, f):
        loop = asyncio.get_event_loop()
        async def run():
            with await HUT2.connect(target, loop=loop) as dev:
                return await f(dev)
        return loop.run_until_complete(run())

    def test_connect(self):
        async def run(dev):
            pass
        self.with_device(run)

    def test_status(self):
        async def run(dev):
            st = await dev.get_status()
            self.assertGreater(st.temp, 0.)
            self.assertLess(st.temp, 100.)
        self.with_device(run)

    def test_sw(self):
        async def run(dev):
            for s in 0, 1:
                dev.sw(0x7f | (s << 7))
                await asyncio.sleep(.2)
                self.assertEqual((await dev.get_status()).port_states[7], s)
        self.with_device(run)

    def test_sw_onoff(self):
        async def run(dev):
            dev.sw_off(8)
            await asyncio.sleep(.2)
            self.assertEqual((await dev.get_status()).port_states[7], 0)
            dev.sw_on(8)
            await asyncio.sleep(.2)
            self.assertEqual((await dev.get_status()).port_states[7], 1)
        self.with_device(run)

    def test_st(self):
        async def run(dev):
            dev.sw_on(8)
            await asyncio.sleep(.2)
            dev.st_off(8, 1)
            await asyncio.sleep(.2)
            self.assertEqual((await dev.get_status()).port_states[7], 1)
            await asyncio.sleep(1)
            self.assertEqual((await dev.get_status()).port_states[7], 0)
            dev.sw_on(8)
            await asyncio.sleep(.2)
        self.with_device(run)
