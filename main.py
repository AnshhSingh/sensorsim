import asyncio
import json
import logging
import re
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI, HTTPException
from pymongo import DESCENDING

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost:3000",
    "http://0.0.0.0:8080",
]
# Constants
LOG_FILE = Path("out.txt")
SCENARIO_DELAY_S = 1.5  # 1500 ms
MONGO_URI = (
    
)
DB_NAME = "log_db"
COLLECTION_NAME = "log_entries"

# Globals
mongo_client: AsyncIOMotorClient = None
collection = None

async def tail_file(path: Path):
    """
    Async generator yielding new lines as they get written to `path`.
    Waits for the file to appear, then tails its end.
    """
    while not path.exists():
        logger.warning(f"{path} not found, retrying in 1s…")
        await asyncio.sleep(1)

    with path.open("r") as f:
        f.seek(0, 2)  # jump to end
        while True:
            line = await asyncio.to_thread(f.readline)
            if not line:
                await asyncio.sleep(0.1)
                continue
            yield line.rstrip("\n")

async def updater():
    """
    Continuously buffer incoming lines, extract full JSON objects by brace-matching,
    clean control characters, parse with strict=False, insert into MongoDB, then wait.
    """
    buffer = ""
    async for raw in tail_file(LOG_FILE):
        buffer += raw + "\n"

        # Try to pull out every complete {...} chunk in buffer
        while True:
            start = buffer.find("{")
            if start < 0:
                # No opening brace → discard all
                buffer = ""
                break

            level = 0
            end = None
            for i, ch in enumerate(buffer[start:], start):
                if ch == "{":
                    level += 1
                elif ch == "}":
                    level -= 1
                    if level == 0:
                        end = i + 1
                        break

            if end is None:
                # Incomplete → wait for more lines
                break

            # Extract and remove this JSON candidate
            candidate = buffer[start:end]
            buffer = buffer[end:]

            # Strip raw control characters (0x00–0x1F)
            cleaned = re.sub(r"[\x00-\x1F]+", "", candidate)

            # Parse allowing embedded escapes
            try:
                doc = json.loads(cleaned, strict=False)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON: {e!r} — data: {cleaned!r}")
                # Skip this chunk, but keep scanning buffer
                continue

            # Timestamp, insert, and then pause to match simulation
            doc["created_at"] = datetime.utcnow()
            try:
                await collection.insert_one(doc)
                logger.debug(f"Inserted document: {doc}")
            except Exception as e:
                logger.error(f"MongoDB insert error: {e!r}")

            await asyncio.sleep(SCENARIO_DELAY_S)
            # Loop again in case buffer has additional complete objects

@asynccontextmanager
async def lifespan(app: FastAPI):
    global mongo_client, collection

    # 1) Establish MongoDB connection & index
    mongo_client = AsyncIOMotorClient(MONGO_URI)
    collection = mongo_client[DB_NAME][COLLECTION_NAME]
    await collection.create_index([("created_at", DESCENDING)])

    # 2) Launch background tail-and-insert task
    task = asyncio.create_task(updater())
    yield  # FastAPI starts serving here

    # 3) On shutdown, cancel and clean up
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        logger.info("Updater task cancelled cleanly")
    mongo_client.close()
    logger.info("MongoDB connection closed")

# Initialize FastAPI with custom lifespan
app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/data")
async def get_all_data(limit: int = 100):
    """
    Fetch up to `limit` most recent records.
    """
    try:
        cursor = collection.find().sort("created_at", DESCENDING).limit(limit)
        docs = await cursor.to_list(length=limit)
    except Exception as e:
        logger.error(f"Database error: {e!r}")
        raise HTTPException(500, "Database error")

    if not docs:
        raise HTTPException(404, "No data found")

    # Make JSON-serializable
    for d in docs:
        d["_id"] = str(d["_id"])
        d["created_at"] = d["created_at"].isoformat()
    return docs

@app.get("/latest")
async def get_latest_entry():
    """
    Fetch the single most recent record.
    """
    try:
        doc = await collection.find_one(sort=[("created_at", DESCENDING)])
    except Exception as e:
        logger.error(f"Database error: {e!r}")
        raise HTTPException(500, "Database error")

    if not doc:
        raise HTTPException(404, "No data found")

    doc["_id"] = str(doc["_id"])
    doc["created_at"] = doc["created_at"].isoformat()
    return doc
