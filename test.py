import logging
import asyncio

from hut2 import HUT2


def main():
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    loop.set_debug(False)
    async def run():
        with await HUT2.connect("opticlock", loop=loop) as dev:
            print(await dev.get_status())
            await asyncio.sleep(.2)
            dev.sw(0x7f)
            await asyncio.sleep(.2)
            dev.sw(0xff)
            await asyncio.sleep(.2)
            dev.sw_off(8)
            await asyncio.sleep(.2)
            assert (await dev.get_status()).port_states[8 - 1] == 0
            await asyncio.sleep(.2)
            dev.sw_on(8)
            await asyncio.sleep(.2)
            assert (await dev.get_status()).port_states[8 - 1] == 1
            await asyncio.sleep(.2)
            dev.st_off(8, 1)
            await asyncio.sleep(.2)
            assert (await dev.get_status()).port_states[8 - 1] == 1
            await asyncio.sleep(1)
            assert (await dev.get_status()).port_states[8 - 1] == 0
    loop.run_until_complete(run())


if __name__ == "__main__":
    main()

