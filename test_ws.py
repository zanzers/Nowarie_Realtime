import asyncio
import websockets


async def main():
    uri = "ws://127.0.0.1:8000/ws"

    try:
        async with websockets.connect(uri) as websocket:
            print("Connected successfully!")

            await websocket.send("Hello Nowarie")
            response = await websocket.recv()

            print(f"Server response: {response}")

    except Exception as error:
        print(f"Connection failed: {error}")


asyncio.run(main())