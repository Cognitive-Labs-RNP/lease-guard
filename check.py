import asyncio
import json
from pathlib import Path

from rocketride import RocketRideClient


async def main() -> None:
    pipeline_path = Path(__file__).resolve().parent / "pipelines" / "lease_extraction.pipe"
    pipeline = json.loads(pipeline_path.read_text(encoding="utf-8"))

    try:
        client = RocketRideClient()
        async with client:
            validation = await client.validate(pipeline, source="chat_1")
    except ConnectionError:
        print("RocketRide validation could not connect. Check ROCKETRIDE_URI and ROCKETRIDE_APIKEY, then run check.py again.")
        raise SystemExit(2)

    print(json.dumps({
        "valid": True,
        "pipeline_has_errors": bool(validation.get("errors", [])),
        "errors": validation.get("errors", []),
        "warnings": validation.get("warnings", []),
    }, indent=2))
    if validation.get("errors"):
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
