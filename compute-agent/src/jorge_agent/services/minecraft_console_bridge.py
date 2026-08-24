import asyncio

from fastapi import WebSocket

from jorge_agent.services.rcon_service import (
    RconError,
    execute_rcon_command,
)


async def bridge_minecraft_console(
    name: str,
    websocket: WebSocket,
) -> None:
    await websocket.accept()

    while True:
        command = await websocket.receive_text()

        command = command.strip()

        if not command:
            continue

        try:
            response = await asyncio.to_thread(
                execute_rcon_command,
                name,
                command,
            )

            await websocket.send_json(
                {
                    "type": "response",
                    "command": command,
                    "response": response,
                }
            )

        except RconError as exc:
            await websocket.send_json(
                {
                    "type": "error",
                    "command": command,
                    "error": str(exc),
                }
            )

        except OSError as exc:
            await websocket.send_json(
                {
                    "type": "error",
                    "command": command,
                    "error": (
                        f"RCON unavailable: {exc}"
                    ),
                }
            )

