import pytest
from domain.model import *
from datetime import date

def test_adding_transaction_updates_amounts_paid_by_person():
    group = Group("group1", "EUR")

    person1 = Person("person1")
    person2 = Person("person2")

    group.add_person(person1)
    group.add_person(person2)

    transaction = Transaction(person1, 200, "EUR", [person1, person2], [100, 100], "Spesa", date.today())

    group.add_transaction(transaction)

    assert group.amounts_paid[person1] == 100
    assert group.amounts_paid[person2] == 100

def test_adding_transaction_updates_debt_quantities():
    group = Group("group1", "EUR")

    person1 = Person("person1")
    person2 = Person("person2")

    group.add_person(person1)
    group.add_person(person2)

    transaction = Transaction(person1, 200, "EUR", [person1, person2], [100, 100], "Spesa", date.today())

    group.add_transaction(transaction)

    debt1 = Debt(person2, person1, 100)

    assert debt1 in group.debts 


def test_can_add_person_in_group():
    group = Group("group1", "EUR")

    person1 = Person("person1")
    person2 = Person("person2")

    group.add_person(person1)
    group.add_person(person2)

    assert person1 in group.persons  
    assert person2 in group.persons  

def test_can_remove_person_from_group():
    group = Group("group1", "EUR")

    person1 = Person("person1")
    person2 = Person("person2")

    group.add_person(person1)
    group.add_person(person2)
    group.remove_person(person2)

    assert person1 in group.persons  
    assert person2 not in group.persons

def test_removing_person_when_debt_exists():
    group = Group("group1", "EUR")

    person1 = Person("person1")
    person2 = Person("person2")

    group.add_person(person1)
    group.add_person(person2)

    transaction = Transaction(person1, 200, "EUR", [person1, person2], [100, 100], "Spesa", date.today())

    group.add_transaction(transaction)

    debt1 = Debt(person2, person1, 100)

    group.remove_person(person2)
    group.remove_person(person1)

    assert debt1 in group.debts   

def test_calculate_net_debts():
    person1 = Person("person1")
    person2 = Person("person2")
    person3 = Person("person3")

    debt1 = Debt(person1, person2, 50)
    debt2 = Debt(person2, person3, 30)
    debt3 = Debt(person1, person3, 20)

    debts = [debt1, debt2, debt3]

    net_balances = get_net_owed_balances(debts)

    assert net_balances[person1] == -70
    assert net_balances[person2] == +20
    assert net_balances[person3] == +50

def test_minimize_debts():
    person1 = Person("person1")
    person2 = Person("person2")
    person3 = Person("person3")

    debt1 = Debt(person1, person2, 50)
    debt2 = Debt(person2, person3, 30)
    debt3 = Debt(person1, person3, 20)

    debts = [debt1, debt2, debt3]  

    minimized_debts = minimize_debts(debts)

    assert len(minimized_debts) == 2
    assert Debt(person1, person2, 20) in minimized_debts
    assert Debt(person1, person3, 50) in minimized_debts

def test_minimize_debts_no_debts():
    debts = []
    minimized_debts = minimize_debts(debts)
    assert minimized_debts == []

def test_minimize_debts_all_settled():
    person1 = Person("person1")
    person2 = Person("person2")

    debt1 = Debt(person1, person2, 50)
    debt2 = Debt(person2, person1, 50)

    debts = [debt1, debt2]

    minimized_debts = minimize_debts(debts)

    assert minimized_debts == []


def test_minimize_debts_single_person():
    person1 = Person("person1")

    debts = []

    minimized_debts = minimize_debts(debts)

    assert minimized_debts == []

def test_rename_person():

    person = Person("old_name")

    person.name = "new_name"
    assert person.name == "new_name"

def test_debt_greater_than_other_debt():
    person1 = Person("person1")
    person2 = Person("person2")

    debt1 = Debt(person1, person2, 100)
    debt2 = Debt(person2, person1, 30)

    assert debt1 > debt2

def test_add_multiple_transactions_and_check_debts():
    group = Group("group1", "EUR")

    person1 = Person("person1")
    person2 = Person("person2")

    group.add_person(person1)
    group.add_person(person2)

    transaction1 = Transaction(person1, 300, "EUR", [person1, person2], [150, 150], "Spesa1", date.today())
    transaction2 = Transaction(person2, 200, "EUR", [person1, person2], [100, 100], "Spesa2", date.today())
    transaction3 = Transaction(person1, 100, "EUR", [person1, person2], [50, 50], "Spesa3", date.today())

    group.add_transaction(transaction1)
    group.add_transaction(transaction2)
    group.add_transaction(transaction3)

    net_balances = get_net_owed_balances(group.debts)

    assert net_balances[person1] == -100
    assert net_balances[person2] == +100

def test_remove_transaction_and_check_debts():
    group = Group("group1", "EUR")

    person1 = Person("person1")
    person2 = Person("person2")

    group.add_person(person1)
    group.add_person(person2)

    transaction1 = Transaction(person1, 300, "EUR", [person1, person2], [150, 150], "Spesa1", date.today())
    transaction2 = Transaction(person2, 200, "EUR", [person1, person2], [100, 100], "Spesa2", date.today())
    transaction3 = Transaction(person1, 1000, "EUR", [person1, person2], [500, 500], "Spesa3", date.today())

    group.add_transaction(transaction1)
    group.add_transaction(transaction2)
    group.add_transaction(transaction3)

    group.remove_transaction(transaction3)

    net_balances = get_net_owed_balances(group.debts)

    assert net_balances[person1] == -50
    assert net_balances[person2] == +50

def test_different_currencies_in_transaction():
    group = Group("group1", "EUR")

    person1 = Person("person1")
    person2 = Person("person2")

    group.add_person(person1)
    group.add_person(person2)

    transaction = Transaction(person1, 200, "USD", [person1, person2], [100, 100], "Spesa", date.today())
    group.add_transaction(transaction)

    assert group.amounts_paid[person2] == 100*get_convertion_rate(transaction.currency, group.currency)
    debt1 = Debt(person2, person1, 100*get_convertion_rate(transaction.currency, group.currency)) 
    assert debt1 in group.debts


    