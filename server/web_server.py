import asyncio

from websockets.asyncio.server import serve
from websockets.asyncio.server import ServerConnection
import websockets


async def handler(websocket : ServerConnection):
    while True:
        await websocket.send('GameStartingW', text=True)
        try:
            message = await websocket.recv()
        except websockets.exceptions.ConnectionClosedOK:
            break
        print(message)
        await websocket.close()
        return


async def main():
    async with serve(handler, "", 7999):
        await asyncio.get_running_loop().create_future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())