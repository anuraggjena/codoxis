from fastapi import HTTPException


def require_ai_result(result: str | None, feature: str) -> str:
    if not result:
        raise HTTPException(status_code=503, detail=f"AI unavailable for {feature}")
    return result
