import json
import pathlib

from fastapi import APIRouter

router = APIRouter()

_CARS_PATH = pathlib.Path(__file__).resolve().parent.parent.parent / "data" / "cars.json"
_cars_data: dict | None = None


def _load_cars() -> dict:
    global _cars_data
    if _cars_data is None:
        with open(_CARS_PATH) as f:
            _cars_data = json.load(f)
    return _cars_data


@router.get("/api/cars")
async def get_cars():
    return _load_cars()
