"""FastAPI application: Twilio voice webhook, health check, and media stream bridge."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Optional

import websockets
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.websockets import WebSocketDisconnect
from twilio.request_validator import RequestValidator
from twilio.rest import Client as TwilioRestClient
from twilio.twiml.voice_response import Connect, VoiceResponse

from receptionist.config import ConfigError, load_config
from receptionist.realtime_bridge import MediaBridge

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("receptionist.app")

OPENAI_REALTIME_URL = "wss://api.openai.com/v1/realtime?model=gpt-realtime"

app = FastAPI(title="AI Receptionist")


def _config_path() -> str:
    return os.getenv("BUSINESS_CONFIG_PATH", "business.yaml")


def _signature_validation_enabled() -> bool:
    return os.getenv("VALIDATE_TWILIO_SIGNATURE", "true").lower() != "false"


def _load_config_or_none():
    try:
        return load_config(_config_path())
    except ConfigError as exc:
        logger.error("Configuration error: %s", exc)
        return None


def _twilio_rest_client() -> Optional[TwilioRestClient]:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    if account_sid and auth_token:
        return TwilioRestClient(account_sid, auth_token)
    return None


@app.get("/health")
async def health() -> JSONResponse:
    config = _load_config_or_none()
    return JSONResponse(
        {
            "status": "ok" if config is not None else "config_error",
            "business": config.business.name if config else None,
        }
    )


def validate_twilio_signature(request: Request, form: dict) -> bool:
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    if not _signature_validation_enabled() or not auth_token:
        return True
    signature = request.headers.get("X-Twilio-Signature", "")
    validator = RequestValidator(auth_token)
    url = str(request.url)
    return validator.validate(url, form, signature)


@app.post("/voice")
async def voice(request: Request) -> HTMLResponse:
    form = dict(await request.form())

    if not validate_twilio_signature(request, form):
        return PlainTextResponse("Invalid signature", status_code=403)

    config = _load_config_or_none()
    response = VoiceResponse()

    if config is None:
        response.say("Sorry, this receptionist is not configured correctly.")
        response.hangup()
        return HTMLResponse(content=str(response), media_type="application/xml")

    host = request.url.hostname
    connect = Connect()
    connect.stream(url=f"wss://{host}/media-stream")
    response.append(connect)
    return HTMLResponse(content=str(response), media_type="application/xml")


@app.websocket("/media-stream")
async def media_stream(websocket: WebSocket) -> None:
    await websocket.accept()

    config = _load_config_or_none()
    if config is None:
        await websocket.close()
        return

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("OPENAI_API_KEY is not set, closing media stream.")
        await websocket.close()
        return

    call_sid: Optional[str] = None
    from_number: Optional[str] = None
    bridge: Optional[MediaBridge] = None

    async with websockets.connect(
        OPENAI_REALTIME_URL,
        additional_headers={"Authorization": f"Bearer {openai_api_key}"},
    ) as openai_ws:

        async def openai_send(payload: str) -> None:
            await openai_ws.send(payload)

        async def twilio_send(payload: dict) -> None:
            await websocket.send_json(payload)

        async def receive_from_twilio() -> None:
            nonlocal call_sid, from_number, bridge
            try:
                async for message in websocket.iter_text():
                    data = json.loads(message)
                    if data.get("event") == "start" and bridge is None:
                        call_sid = data["start"].get("callSid", "unknown")
                        from_number = data["start"].get("customParameters", {}).get("from")
                        bridge = MediaBridge(
                            config,
                            call_sid=call_sid,
                            from_number=from_number,
                            dry_run=False,
                            twilio_rest_client=_twilio_rest_client(),
                        )
                        await openai_send(json.dumps(bridge.session_update_event()))
                        for greeting_event in bridge.greeting_events():
                            await openai_send(json.dumps(greeting_event))
                    if bridge is not None:
                        await bridge.handle_twilio_message(message, openai_send)
            except WebSocketDisconnect:
                logger.info("Twilio client disconnected.")

        async def send_to_twilio() -> None:
            try:
                async for message in openai_ws:
                    if bridge is not None:
                        await bridge.handle_openai_message(message, openai_send, twilio_send)
                        if bridge.should_close:
                            await websocket.close()
                            break
            except websockets.ConnectionClosed:
                logger.info("OpenAI realtime connection closed.")

        await asyncio.gather(receive_from_twilio(), send_to_twilio())

    if bridge is not None:
        bridge.finish()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 5050)))
