from domain.model import *
from datetime import date


def test_adding_transaction_updates_total_share_by_person():
    group = Group("group1", "EUR")

    person1 = Person("luigi")
    person2 = Person("mario")

    group.add_person(person1)
    group.add_person(person2)
    
    share1 = DebtorShare(person1, 100)
    share2 = DebtorShare(person2, 100)
    
    share3 = DebtorShare(person2, 200)

    transaction = Transaction(person1, 200, "EUR", [share1, share2], "Trip", date.today())

    group.add_transaction(transaction)

    assert group.total_share[person1] == 100
    assert group.total_share[person2] == 100
    
    transaction2 = Transaction(person1, 200, "EUR", [share3], "Trip", date.today())
    group.add_transaction(transaction2)
    
    assert group.total_share[person2] == 300

def test_adding_transaction_updates_debt_quantities():
    group = Group("group1", "EUR")

    person1 = Person("luigi")
    person2 = Person("mario")
    
    share1 = DebtorShare(person1, 100)
    share2 = DebtorShare(person2, 100)

    group.add_person(person1)
    group.add_person(person2)

    transaction = Transaction(person1, 200, "EUR", [share1, share2], "Trip", date.today())

    group.add_transaction(transaction)

    debt1 = Debt(person2, person1, 100)

    assert debt1 in group.debts 

def test_removing_person_when_debt_exists():
    group = Group("group1", "EUR")

    person1 = Person("Luigi")
    person2 = Person("Mario")

    group.add_person(person1)
    group.add_person(person2)

    share1 = DebtorShare(person1, 100)
    share2 = DebtorShare(person2, 100)
    share3 = DebtorShare(person2, 200)
    
    transaction = Transaction(person1, 200, "EUR", [share1, share2], "Trip", date.today())

    group.add_transaction(transaction)

    debt1 = Debt(person2, person1, 100)

    group.remove_person(person2)
    group.remove_person(person1)

    assert debt1 in group.debts   

def test_calculate_net_debts():
    person1 = Person("Luigi")
    person2 = Person("Mario")
    person3 = Person("Peach")

    debt1 = Debt(person1, person2, 50)
    debt2 = Debt(person2, person3, 30)
    debt3 = Debt(person1, person3, 20)

    debts = [debt1, debt2, debt3]

    net_balances = get_net_owed_balances(debts)

    assert net_balances[person1] == -70
    assert net_balances[person2] == +20
    assert net_balances[person3] == +50

def test_minimize_debts():
    person1 = Person("Luigi")
    person2 = Person("Mario")
    person3 = Person("Peach")

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
    person1 = Person("Luigi")
    person2 = Person("Mario")

    debt1 = Debt(person1, person2, 50)
    debt2 = Debt(person2, person1, 50)

    debts = [debt1, debt2]

    minimized_debts = minimize_debts(debts)

    assert minimized_debts == []


def test_minimize_debts_single_person():
    person1 = Person("Luigi")

    debts = []

    minimized_debts = minimize_debts(debts)

    assert minimized_debts == []


def test_debt_greater_than_other_debt():
    person1 = Person("Luigi")
    person2 = Person("Mario")

    debt1 = Debt(person1, person2, 100)
    debt2 = Debt(person2, person1, 30)

    assert debt1 > debt2

def test_add_multiple_transactions_and_check_debts():
    group = Group("group1", "EUR")

    person1 = Person("Luigi")
    person2 = Person("Mario")

    group.add_person(person1)
    group.add_person(person2)
    
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

    net_balances = get_net_owed_balances(group.debts)

    assert net_balances[person1] == -100
    assert net_balances[person2] == +100

def test_remove_transaction_and_check_debts():
    group = Group("group1", "EUR")

    person1 = Person("Luigi")
    person2 = Person("Mario")

    group.add_person(person1)
    group.add_person(person2)

    share1 = DebtorShare(person1, 150)
    share2 = DebtorShare(person2, 150)
    share3 = DebtorShare(person1, 100)
    share4 = DebtorShare(person2, 100)
    share5 = DebtorShare(person1, 500)
    share6 = DebtorShare(person2, 500)
    
    transaction1 = Transaction(person1, 300, "EUR", [share1, share2], "Spesa1", date.today())
    transaction2 = Transaction(person2, 200, "EUR", [share3, share4], "Spesa2", date.today())
    transaction3 = Transaction(person1, 1000, "EUR", [share5, share6], "Spesa3", date.today())

    group.add_transaction(transaction1)
    group.add_transaction(transaction2)
    group.add_transaction(transaction3)

    group.remove_transaction(transaction3)

    net_balances = get_net_owed_balances(group.debts)

    assert net_balances[person1] == -50
    assert net_balances[person2] == +50
    
    assert group.total_share[person1] == 250

def test_different_currencies_in_transaction():
    group = Group("group1", "EUR")

    person1 = Person("Luigi")
    person2 = Person("Mario")

    group.add_person(person1)
    group.add_person(person2)

    share1 = DebtorShare(person1, 100)
    share2 = DebtorShare(person2, 100)

    transaction = Transaction(person1, 200, "EUR", [share1, share2], "Spesa", date.today())
    group.add_transaction(transaction)

    assert group.total_share[person2] == 100*get_convertion_rate(transaction.currency, group.currency)
    debt1 = Debt(person2, person1, 100*get_convertion_rate(transaction.currency, group.currency)) 
    assert debt1 in group.debts
    assert group.total_share == {person1: 100, person2: 100}

    