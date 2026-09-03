from fastapi import APIRouter

router = APIRouter()

@router.get("/token")
def token():
    return {}