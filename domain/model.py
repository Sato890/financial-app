from typing import Optional
import uuid
from dataclasses import dataclass, field
import heapq
from typing import List, Optional
from datetime import date
from domain.convertion_rates import conversion_rates

class Person:
    def __init__(self, name: str, id: Optional[str] = None):
        self.name = name
        self.id = id or uuid.uuid4()

    def __eq__(self, other):
        if not isinstance(other, Person):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)
    
    def __repr__(self):
        return f"Person(name={self.name})"
    
    def __str__(self):
        return self.name


@dataclass
class DebtorShare:
    debtor: "Person"
    split_amount: float

@dataclass(order=True)
class Debt: 
    debtor: Person = field(compare=False)
    creditor: Person = field(compare=False)
    amount: float

class Transaction:
    def __init__(self, who_paid: Person, amount: float, currency: str, debtor_shares: List[DebtorShare], category: str, date_time: date, id: Optional[str] = None):
        self.who_paid = who_paid
        self.amount = amount
        self.currency = currency
        self.debtor_shares = debtor_shares
        self.category = category
        self.date_time = date_time
        self.id = id or uuid.uuid4()

    def __repr__(self):
        return (
            f"Transaction("
            f"who_paid={self.who_paid}, "
            f"amount={self.amount}, "
            f"currency={self.currency}, "
            f"debtor_shares={self.debtor_shares}, "
            f"category={self.category}, "
            f"date_time={self.date_time})"
        )
        
    def __eq__(self, other):
        return isinstance(other, Transaction) and self.id == other.id

    def __hash__(self):
        return hash(self.id)
    
class Group:
    def __init__(self, name: str, currency: str, id: Optional[str] = None):
        self.id = id or uuid.uuid4()
        self.name = name
        self.currency = currency
        self.persons = set()
        self.transactions = []
        self.debts = []            

    def __repr__(self):
        return f"Group(\nname={self.name},\n currency={self.currency},\n persons={self.persons},\n transactions={len(self.transactions)},\n debts={get_net_owed_balances(self.debts)},\n amounts_paid={self.total_share}\n)"
    
    def add_person(self, person: Person): 
        self.persons.add(person)

    def remove_person(self, person: Person): 
        self.persons.remove(person)

    def add_transaction(self, transaction: Transaction):
        self.transactions.append(transaction)
        self._recalculate_debts()

    def remove_transaction(self, transaction: Transaction):
        self.transactions.remove(transaction)
        self._recalculate_debts()
    
    def _recalculate_debts(self):
        raw_debts = []
        for t in self.transactions:
            for ds in t.debtor_shares:
                if ds.debtor != t.who_paid:
                    amount = -ds.split_amount * get_convertion_rate(t.currency, self.currency)
                    raw_debts.append(Debt(debtor=ds.debtor, creditor=t.who_paid, amount=amount))
        self.debts = minimize_debts(raw_debts)

    @property
    def total_share(self) -> dict:
        shares = {}
        for t in self.transactions:
            for ds in t.debtor_shares:
                shares[ds.debtor] = shares.get(ds.debtor, 0) + ds.split_amount
        return shares

    def add_person(self, person: Person): 
        self.persons.add(person)

    def remove_person(self, person: Person): 
        self.persons.remove(person)

    def _add_debt(self, debt: Debt):
        self.debts.append(debt)

def get_net_owed_balances(debts: List[Debt]) -> dict:
        owed_balances = {}

        for debt in debts:
            owed_balances[debt.debtor] = owed_balances.get(debt.debtor, 0) - debt.amount
            owed_balances[debt.creditor] = owed_balances.get(debt.creditor, 0) + debt.amount

        return owed_balances


def minimize_debts(debts: List[Debt]) -> List[Debt]:
    
    net_debts = get_net_owed_balances(debts)
    negative_debts = []
    positive_debts = []

    index_person = 0
    for person, amount in net_debts.items():
        if amount < 0:
            heapq.heappush(negative_debts, (amount, index_person, person))
        elif amount > 0:
            heapq.heappush(positive_debts, (amount, index_person, person))
        
        index_person += 1
    
    settlements = [] 

    while negative_debts and positive_debts:

        neg_amount, index_debtor, debtor = heapq.heappop(negative_debts)
        pos_amount, index_creditor, creditor = heapq.heappop(positive_debts)

        settlement_amount = min(-neg_amount, pos_amount)

        settlements.append(Debt(debtor, creditor, settlement_amount))

        new_neg_amount = neg_amount + settlement_amount
        new_pos_amount = pos_amount - settlement_amount

        if new_neg_amount < 0:
            heapq.heappush(negative_debts, (new_neg_amount, index_debtor, debtor))
        if new_pos_amount > 0:
            heapq.heappush(positive_debts, (new_pos_amount, index_creditor, creditor))

    return [d for d in settlements if abs(d.amount) > 0]

def get_convertion_rate(from_currency: str, to_currency: str) -> float:
    if from_currency == to_currency:
        return 1.0
    try:
        return conversion_rates[(from_currency, to_currency)]
    except KeyError:
        try:
            return 1 / conversion_rates[(to_currency, from_currency)]
        except KeyError:
            raise ValueError(f"No conversion rate available for {from_currency} to {to_currency}")