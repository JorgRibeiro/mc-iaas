import asyncio

from fastapi import WebSocket

from jorge_agent.services.console_service import (
    InstanceConsole,
)


async def _console_to_websocket(
    console: InstanceConsole,
    websocket: WebSocket,
) -> None:
    while True:
        data = await asyncio.to_thread(
            console.read,
            4096,
        )

        if not data:
            break

        await websocket.send_text(
            data.decode(
                "utf-8",
                errors="replace",
            )
        )


async def _websocket_to_console(
    console: InstanceConsole,
    websocket: WebSocket,
) -> None:
    while True:
        data = await websocket.receive_text()

        await asyncio.to_thread(
            console.write,
            data.encode("utf-8"),
        )


async def bridge_instance_console(
    name: str,
    websocket: WebSocket,
) -> None:
    console = InstanceConsole(name)

    try:
        console.open()

        await websocket.accept()

        console_reader = asyncio.create_task(
            _console_to_websocket(
                console,
                websocket,
            )
        )

        websocket_reader = asyncio.create_task(
            _websocket_to_console(
                console,
                websocket,
            )
        )

        done, pending = await asyncio.wait(
            {
                console_reader,
                websocket_reader,
            },
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()

        await asyncio.gather(
            *pending,
            return_exceptions=True,
        )

        for task in done:
            exception = task.exception()

            if exception is not None:
                raise exception

    finally:
        console.close()
