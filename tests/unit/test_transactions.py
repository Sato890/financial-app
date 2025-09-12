from domain.model import *
from datetime import date

import pytest
from domain.model import *
from datetime import date

@pytest.fixture
def person1():
    return Person("luigi")

@pytest.fixture
def person2():
    return Person("mario")

@pytest.fixture
def person3():
    return Person("peach")

@pytest.fixture
def group(person1, person2):
    group = Group("group1", "EUR")
    group.add_person(person1)
    group.add_person(person2)
    return group

@pytest.fixture
def group_with_transaction(group, person1, person2):
    share1 = DebtorShare(person1, 10000)
    share2 = DebtorShare(person2, 10000)
    transaction = Transaction(person1, 200, "EUR", [share1, share2], "Trip", date.today())
    group.add_transaction(transaction)
    return group

def test_adding_transaction_updates_total_share_by_person(group, person1, person2):
    
    share1 = DebtorShare(person1, 10000)
    share2 = DebtorShare(person2, 10000)

    assert share1.split_amount_cents == 10000
    assert share1.split_amount == 100
    
    share3 = DebtorShare(person2, 20000)

    transaction = Transaction(person1, 200, "EUR", [share1, share2], "Trip", date.today())
    
    assert transaction.amount == 200

    group.add_transaction(transaction)

    assert group.total_share[person1] == 100
    assert group.total_share[person2] == 100
    
    transaction2 = Transaction(person1, 200, "EUR", [share3], "Trip", date.today())
    group.add_transaction(transaction2)
    
    assert group.total_share[person2] == 300

def test_adding_transaction_updates_debt_quantities(group_with_transaction):

    debt1 = Debt(person2, person1, 10000)

    assert debt1.amount_cents == 10000

    assert debt1 in group_with_transaction.debts 

def test_removing_person_when_debt_exists(group_with_transaction, person1, person2):
    debt1 = Debt(person2, person1, 10000)

    group_with_transaction.remove_person(person2)
    group_with_transaction.remove_person(person1)

    assert debt1 in group_with_transaction.debts   

def test_calculate_net_debts(person1, person2, person3):
    debt1 = Debt(person1, person2, 50)
    debt2 = Debt(person2, person3, 30)
    debt3 = Debt(person1, person3, 20)

    debts = [debt1, debt2, debt3]

    net_balances = get_net_owed_balances_cents(debts)

    assert net_balances[person1] == -70
    assert net_balances[person2] == +20
    assert net_balances[person3] == +50

def test_minimize_debts(person1, person2, person3):
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

def test_minimize_debts_all_settled(person1, person2):
    debt1 = Debt(person1, person2, 50)
    debt2 = Debt(person2, person1, 50)

    debts = [debt1, debt2]

    minimized_debts = minimize_debts(debts)

    assert minimized_debts == []


def test_minimize_debts_single_person():
    debts = []

    minimized_debts = minimize_debts(debts)

    assert minimized_debts == []


def test_debt_greater_than_other_debt(person1, person2):
    debt1 = Debt(person1, person2, 100)
    debt2 = Debt(person2, person1, 30)

    assert debt1 > debt2

def test_add_multiple_transactions_and_check_debts(group, person1, person2):

    share1 = DebtorShare(person1, 150)
    share2 = DebtorShare(person2, 150)
    share3 = DebtorShare(person1, 100)
    share4 = DebtorShare(person2, 100)
    share5 = DebtorShare(person1, 50)
    share6 = DebtorShare(person2, 50)
    
    transaction1 = Transaction(person1, 300, "EUR", [share1, share2], "Spesa1", date.today())
    transaction2 = Transaction(person2, 200, "EUR", [share3, share4], "Spesa2", date.today())
    transaction3 = Transaction(person1, 100, "EUR", [share5, share6], "Spesa3", date.today())

    group.add_transaction(transaction1)
    group.add_transaction(transaction2)
    group.add_transaction(transaction3)

    net_balances = get_net_owed_balances_cents(group.debts)

    assert net_balances[person1] == -100
    assert net_balances[person2] == +100

def test_remove_transaction_and_check_debts(group, person1, person2):
    share1 = DebtorShare(person1, 15000)
    share2 = DebtorShare(person2, 15000)
    share3 = DebtorShare(person1, 10000)
    share4 = DebtorShare(person2, 10000)
    share5 = DebtorShare(person1, 50000)
    share6 = DebtorShare(person2, 50000)
    
    transaction1 = Transaction(person1, 300, "EUR", [share1, share2], "Spesa1", date.today())
    transaction2 = Transaction(person2, 200, "EUR", [share3, share4], "Spesa2", date.today())
    transaction3 = Transaction(person1, 1000, "EUR", [share5, share6], "Spesa3", date.today())

    group.add_transaction(transaction1)
    group.add_transaction(transaction2)
    group.add_transaction(transaction3)

    group.remove_transaction(transaction3)

    net_balances = get_net_owed_balances_cents(group.debts)

    assert net_balances[person1] == -5000
    assert net_balances[person2] == +5000
    
    assert group.total_share[person1] == 250

def test_different_currencies_in_transaction(group, person1, person2):
    share1 = DebtorShare(person1, 10000)
    share2 = DebtorShare(person2, 10000)

    transaction = Transaction(person1, 200, "USD", [share1, share2], "Spesa", date.today())
    group.add_transaction(transaction)

    assert group.total_share[person2] == 100*get_convertion_rate(transaction.currency, group.currency)

    debt1 = Debt(person2, person1, 10000*get_convertion_rate(transaction.currency, group.currency)) 

    assert debt1 in group.debts
    total_share_person1 = 100*get_convertion_rate(transaction.currency, group.currency)
    total_share_person2 = 100*get_convertion_rate(transaction.currency, group.currency)
    assert group.total_share == {person1: total_share_person1, person2: total_share_person2}
