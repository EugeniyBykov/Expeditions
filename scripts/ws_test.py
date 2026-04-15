import asyncio
import websockets

URLS = [
    "ws://localhost:8000/ws?token=token",
    "ws://localhost:8000/ws?token=token",
    "ws://localhost:8000/ws?token=token",
]


async def handle_connection(name: str, url: str) -> None:
    try:
        async with websockets.connect(url) as ws:
            print(f"[{name}] connected")

            await ws.send(f"hello from {name}")

            while True:
                try:
                    msg = await ws.recv()
                    print(f"[{name}] received: {msg}")
                except websockets.ConnectionClosed as e:
                    print(f"[{name}] closed: code={e.code}, reason={e.reason}")
                    break

    except Exception as e:
        print(f"[{name}] connection error: {e}")


async def main() -> None:
    tasks = [
        asyncio.create_task(handle_connection(f"conn-{i+1}", url))
        for i, url in enumerate(URLS)
    ]

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())