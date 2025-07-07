from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.utils.db import SessionLocal
from app.models.expense import Expense, Share
from app.utils.dsa_utils import simplify_debts

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/simplify")
def simplify_all_debts(db: Session = Depends(get_db)):
    net_balances = {}

    expenses = db.query(Expense).all()
    for exp in expenses:
        shares = db.query(Share).filter(Share.expense_id == exp.id).all()
        for share in shares:
            if share.user_id != exp.paid_by:
                net_balances[share.user_id] = net_balances.get(share.user_id, 0) - share.amount
                net_balances[exp.paid_by] = net_balances.get(exp.paid_by, 0) + share.amount

    simplified = simplify_debts(net_balances)
    return {"settlements": simplified}

@router.get("/leaderboard")
def leaderboard(db: Session = Depends(get_db)):
    from sqlalchemy import func
    from app.models.expense import Expense
    from app.models.user import User

    results = (
        db.query(Expense.paid_by, func.sum(Expense.amount).label("total"))
        .group_by(Expense.paid_by)
        .order_by(func.sum(Expense.amount).desc())
        .limit(5)
        .all()
    )

    board = []
    for uid, total in results:
        user = db.query(User).filter(User.id == uid).first()
        board.append({"user": user.name, "total_paid": total})

    return {"leaderboard": board}

