from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from collections import defaultdict
from heapq import heappush, heappop

from app.schemas.expense_schema import ExpenseCreate
from app.utils.db import SessionLocal
from app.models.expense import Expense, Share
from app.models.transaction import Transaction
from app.models.user import User
from app.auth import get_current_user  # 🔐 Import for JWT user auth

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------------
# ➕ Add Expense
# -------------------------------
@router.post("/add-expense")
def add_expense(expense: ExpenseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_expense = Expense(title=expense.title, amount=expense.amount, paid_by=current_user.id)
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)

    split_amount = round(expense.amount / len(expense.shared_with), 2)

    for uid in expense.shared_with:
        share = Share(expense_id=new_expense.id, user_id=uid, amount=split_amount)
        db.add(share)

        if uid != current_user.id:
            txn = Transaction(
                from_user=uid,
                to_user=current_user.id,
                amount=split_amount,
                date=new_expense.created_at
            )
            db.add(txn)

    db.commit()
    return {"message": "Expense added", "expense_id": new_expense.id}


# -------------------------------
# ⚖️ Get Balances
# -------------------------------
@router.get("/balances")
def get_user_balances(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.id
    balances = {}

    paid_expenses = db.query(Expense).filter(Expense.paid_by == user_id).all()
    for exp in paid_expenses:
        shares = db.query(Share).filter(Share.expense_id == exp.id).all()
        for share in shares:
            if share.user_id != user_id:
                balances[share.user_id] = balances.get(share.user_id, 0) + share.amount

    user_shares = db.query(Share).filter(Share.user_id == user_id).all()
    for share in user_shares:
        exp = db.query(Expense).filter(Expense.id == share.expense_id).first()
        if exp and exp.paid_by != user_id:
            balances[exp.paid_by] = balances.get(exp.paid_by, 0) - share.amount

    formatted = []
    for uid, amt in balances.items():
        if amt > 0:
            formatted.append({"from": uid, "to": user_id, "amount": round(amt, 2)})
        elif amt < 0:
            formatted.append({"from": user_id, "to": uid, "amount": round(-amt, 2)})

    return {"user_id": user_id, "net_balances": formatted}


# -------------------------------
# 📜 Expense History
# -------------------------------
@router.get("/history")
def get_user_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.id
    history = []

    shares = db.query(Share).filter(Share.user_id == user_id).all()
    for share in shares:
        expense = db.query(Expense).filter(Expense.id == share.expense_id).first()
        if expense:
            history.append({
                "expense_id": expense.id,
                "title": expense.title,
                "total_amount": expense.amount,
                "paid_by": expense.paid_by,
                "user_share": share.amount,
                "date": expense.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })

    return {"user_id": user_id, "history": history}


# -------------------------------
# 🤝 Settle-Up Transaction
# -------------------------------
@router.post("/settle-up")
def settle_up(to_user: int, amount: float, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    txn = Transaction(from_user=current_user.id, to_user=to_user, amount=amount)
    db.add(txn)
    db.commit()
    return {"message": f"{current_user.id} paid ₹{amount} to {to_user}"}


# -------------------------------
# 🤖 Simplify Balances
# -------------------------------
@router.get("/simplify")
def simplify_balances(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    balances = defaultdict(lambda: defaultdict(float))
    shares = db.query(Share).join(Expense).all()

    for share in shares:
        payer = share.expense.paid_by
        borrower = share.user_id
        amount = share.amount
        if borrower != payer:
            balances[borrower][payer] += amount

    net_balances = defaultdict(float)
    position = defaultdict(float)

    for u1 in balances:
        for u2 in balances[u1]:
            amt = balances[u1][u2]
            net_balances[(u1, u2)] += amt
            net_balances[(u2, u1)] -= amt
            position[u1] += amt
            position[u2] -= amt

    debtors = []
    creditors = []

    for user, bal in position.items():
        bal = round(bal, 2)
        if bal < 0:
            heappush(debtors, (bal, user))
        elif bal > 0:
            heappush(creditors, (-bal, user))

    result = []
    while debtors and creditors:
        debt_amt, debtor = heappop(debtors)
        cred_amt, creditor = heappop(creditors)
        settle_amt = round(min(-debt_amt, -cred_amt), 2)

        result.append({
            "from": debtor,
            "to": creditor,
            "amount": settle_amt
        })

        debt_amt += settle_amt
        cred_amt += settle_amt

        if round(debt_amt, 2) < 0:
            heappush(debtors, (debt_amt, debtor))
        if round(cred_amt, 2) < 0:
            heappush(creditors, (cred_amt, creditor))

    return result


# -------------------------------
# 💰 Get User Transactions
# -------------------------------
@router.get("/transactions")
def get_user_transactions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.id
    transactions = db.query(Transaction).filter(
        (Transaction.from_user == user_id) | (Transaction.to_user == user_id)
    ).order_by(Transaction.date.desc()).all()

    results = []
    for txn in transactions:
        results.append({
            "id": txn.id,
            "from": txn.from_user,
            "to": txn.to_user,
            "amount": txn.amount,
            "date": txn.date.strftime("%Y-%m-%d %H:%M:%S")
        })

    return {"user_id": user_id, "transactions": results}

@router.get("/history")
def get_expense_history(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    email = user.email  # ← Safely get user from token

    expenses = db.query(Expense).join(ExpenseShare).filter(
        ExpenseShare.user_id == user.id
    ).all()

    history = []
    for exp in expenses:
        user_share = next(
            (s.share_amount for s in exp.shares if s.user_id == user.id), 0
        )
        history.append({
            "expense_id": exp.id,
            "title": exp.title,
            "total_amount": exp.amount,
            "paid_by": exp.paid_by,
            "user_share": user_share,
            "date": str(exp.date)
        })

    return {
        "user_id": user.id,
        "history": history
    }

