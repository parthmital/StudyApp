from fastapi import APIRouter

router = APIRouter()


@router.get("/test")
def test_pyq():
    return {"message": "PYQ matcher is alive"}
