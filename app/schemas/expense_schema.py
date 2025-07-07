from pydantic import BaseModel
from typing import List

class ExpenseCreate(BaseModel):
    title: str
    amount: float
    paid_by: int
    shared_with: List[int]
