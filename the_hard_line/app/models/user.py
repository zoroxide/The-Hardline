from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class UserRecord(BaseModel):
    """Domain model representing an indexed user profile record."""
    id: int
    fbid: Optional[str] = None
    phone: Optional[str] = None
    fname: Optional[str] = None
    sname: Optional[str] = None
    full_name: Optional[str] = None
    gender: Optional[str] = None
    birthday: Optional[str] = None
    fbaccount: Optional[str] = None
    workplace: Optional[str] = None
    job_title: Optional[str] = None
    location: Optional[str] = None
    hometown: Optional[str] = None
    education: Optional[str] = None
    email: Optional[str] = None
    relationship: Optional[str] = None

    @classmethod
    def from_row(cls, row: Any) -> "UserRecord":
        """Map raw database record to structured UserRecord model."""
        fname = row["fname"] or ""
        sname = row["sname"] or ""
        fallback_full_name = f"{fname} {sname}".strip()
        full_name = row["unknown_7"] or fallback_full_name or "UNKNOWN"

        return cls(
            id=row["id"],
            fbid=row["fbid"],
            phone=row["phone"],
            fname=row["fname"],
            sname=row["sname"],
            full_name=full_name,
            gender=row["gender"],
            birthday=row["unknown_4"],
            fbaccount=row["fbaccount"],
            workplace=row["unknown_9"],
            job_title=row["unknown_10"],
            location=row["unknown_11"],
            hometown=row["unknown_12"],
            education=row["unknown_13"],
            email=row["email"],
            relationship=row["unknown_19"]
        )

class SearchResponse(BaseModel):
    """Model representing standardized search query response."""
    query: str
    type: str
    count: int
    duration_ms: float
    results: List[UserRecord]
