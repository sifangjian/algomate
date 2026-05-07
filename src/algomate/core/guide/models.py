from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class GuideAction(BaseModel):
    action: str
    label: str
    target_path: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    available: bool = True


class GuideData(BaseModel):
    available_actions: List[GuideAction]
    message: str
