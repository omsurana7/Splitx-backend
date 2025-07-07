def simplify_debts(net_balances: dict):
    debtors = []
    creditors = []

    for user, balance in net_balances.items():
        if balance < 0:
            debtors.append((user, balance))
        elif balance > 0:
            creditors.append((user, balance))

    debtors.sort(key=lambda x: x[1])               # Most negative first
    creditors.sort(key=lambda x: x[1], reverse=True)  # Most positive first

    result = []
    i, j = 0, 0
    while i < len(debtors) and j < len(creditors):
        debtor, d_amt = debtors[i]
        creditor, c_amt = creditors[j]
        amount = min(-d_amt, c_amt)

        result.append({
            "from": debtor,
            "to": creditor,
            "amount": round(amount, 2)
        })

        d_amt += amount
        c_amt -= amount

        if d_amt == 0:
            i += 1
        else:
            debtors[i] = (debtor, d_amt)
        if c_amt == 0:
            j += 1
        else:
            creditors[j] = (creditor, c_amt)

    return result
