import time
import logging
import asyncio

from hut2 import HUT2


def main():
    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    loop.set_debug(False)
    async def run():
        with await HUT2.connect("opticlock") as dev:
            dev.sw(0xfe)
            await asyncio.sleep(1.)
            dev.sw(0xff)
            print(await dev.ask(b"wer da?"))
    loop.run_until_complete(run())


if __name__ == "__main__":
    main()

