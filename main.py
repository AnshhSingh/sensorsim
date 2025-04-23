import asyncio
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from sse_starlette.sse import EventSourceResponse
from contextlib import asynccontextmanager

LOG_FILE = Path("out.txt")
buffer = []  # in-memory store of all parsed records

async def tail_file(path: Path):

    with path.open("r") as f:
        f.seek(0, 2)  
        while True:
            line = f.readline()
            if not line:
                await asyncio.sleep(0.1)
                continue
            yield line.strip()

async def updater():
    """Background task: read new lines from out.txt and append to buffer."""
    async for raw in tail_file(LOG_FILE):
        try:
            record = json.loads(raw)
            buffer.append(record)
        except json.JSONDecodeError:
            # skip invalid lines
            continue

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: launch the file-watching task
    task = asyncio.create_task(updater())
    yield

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(lifespan=lifespan)

@app.get("/data")
async def get_data():
    """Return all stored records so far."""
    if not buffer:
        raise HTTPException(status_code=404, detail="No data yet")
    return buffer

@app.get("/stream")
async def stream(request: Request):
    """
    Continuous Server-Sent Events (SSE) stream of new records.
    Clients receive each new JSON record as its own SSE message.
    """
    async def event_generator():
        idx = len(buffer)
        while True:
            if await request.is_disconnected():
                break
            # yield any new records
            while idx < len(buffer):
                yield {"data": json.dumps(buffer[idx])}
                idx += 1
            await asyncio.sleep(0.1)

    return EventSourceResponse(event_generator())
