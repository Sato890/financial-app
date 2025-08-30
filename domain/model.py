from dataclasses import dataclass, field
from datetime import date
from typing import List
import heapq
from domain.convertion_rates import conversion_rates

class Person:
    def __init__(self, name: str):
        self.name = name
        self.id = id(self) 

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


class Transaction:
    def __init__(self, who_paid: Person, amount: float, currency: str, debtors: List[Person], split_amounts: List[float], category: str, date_time: date):
        self.who_paid = who_paid
        self.amount = amount
        self.currency = currency
        self.debtors = debtors
        self.split_amounts = split_amounts if split_amounts is not None else [amount / len(debtors)] * len(debtors)
        self.category = category
        self.date_time = date_time
        self.id = id(self)

    def __repr__(self):
        return f"Transaction(who_paid={self.who_paid}, amount={self.amount}, currency={self.currency}, debtors={self.debtors}, split_amounts={self.split_amounts}, purpose={self.purpose}, date_time={self.date_time})"

    def __eq__(self, other):
        if not isinstance(other, Transaction):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

@dataclass(frozen=True, order=True)
class Debt: 
    debtor: Person = field(compare=False)
    creditor: Person = field(compare=False)
    amount: float


class PersonNotInGroup(Exception):
    pass

class TransactionNotInGroup(Exception):
    pass

class PersonAlreadyInGroup(Exception):
    pass

class Group:
    def __init__(self, name: str, currency: str):
        self.name = name
        self.currency = currency
        self.persons = []
        self.transactions = []
        self.debts = []
        self.amounts_paid = {}

    def __repr__(self):
        return f"Group(\nname={self.name},\n currency={self.currency},\n persons={self.persons},\n transactions={len(self.transactions)},\n debts={get_net_owed_balances(self.debts)},\n amounts_paid={self.amounts_paid}\n)"

    def add_transaction(self, transaction: Transaction): 
        self.transactions.append(transaction)
        

        for i in range(len(transaction.debtors)):

            self.amounts_paid[transaction.debtors[i]] = self.amounts_paid.get(transaction.debtors[i], 0) + transaction.split_amounts[i]*get_convertion_rate(transaction.currency, self.currency)

            if transaction.debtors[i] != transaction.who_paid:
                    
                debt1 = Debt(transaction.debtors[i], transaction.who_paid, -transaction.split_amounts[i]*get_convertion_rate(transaction.currency, self.currency))

                self._add_debt(debt1)

        self.debts = minimize_debts(self.debts)


    def add_person(self, person: Person): 
        if person not in self.persons:
            self.persons.append(person)
        else:
            raise PersonAlreadyInGroup(f"Person {person} already in group {self.name}")

    def remove_person(self, person: Person): 
        if person in self.persons:
            self.persons.remove(person)
        else:
            raise PersonNotInGroup(f"Person {person} not in group {self.name}")

    def _add_debt(self, debt: Debt):
        self.debts.append(debt)

    def remove_transaction(self, transaction: Transaction):
        if transaction in self.transactions:
            self.transactions.remove(transaction)
                
            for i in range(len(transaction.debtors)):
                self.amounts_paid[transaction.debtors[i]] -= transaction.split_amounts[i]*get_convertion_rate(transaction.currency, self.currency)
                self._add_debt(Debt(transaction.debtors[i], transaction.who_paid, transaction.split_amounts[i]*get_convertion_rate(transaction.currency, self.currency)))
                
            self.debts = minimize_debts(self.debts)
        else:
            raise TransactionNotInGroup("Transaction not found in group")
    

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