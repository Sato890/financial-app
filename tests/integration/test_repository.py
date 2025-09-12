import uuid
from datetime import date
from sqlalchemy import text
import domain.model as model
import adapters.repository as repository

def test_repository_can_save_a_group(session):
    group = model.Group("group1", "EUR")
    repo = repository.SqlRepository(session)
    
    repo.add(group)
    session.commit()
    
    rows = session.execute(
        text(
            'SELECT name, currency, id FROM "groups"'
        )
    )

    result = [(name, currency, str(id)) for name, currency, id in rows]
    expected = [("group1", "EUR", str(group.id))]

    assert result == expected

def insert_person(session, person_id, name):
    session.execute(
        text("INSERT INTO persons (id, name) VALUES (:id, :name)"),
        {"id": person_id, "name": name},
    )
    return person_id

def insert_group(session, group_id, name, currency):
    session.execute(
        text("INSERT INTO groups (id, name, currency) VALUES (:id, :name, :currency)"),
        {"id": group_id, "name": name, "currency": currency},
    )
    return group_id

def insert_group_person(session, group_id, person_id):
    session.execute(
        text("INSERT INTO group_persons (group_id, person_id) VALUES (:group_id, :person_id)"),
        {"group_id": group_id, "person_id": person_id},
    )

def insert_transaction(session, transaction_id, who_paid_id, group_id, amount_cents, category, currency="EUR"):
    session.execute(
        text(
            "INSERT INTO transactions (id, who_paid_id, amount_cents, currency, category, date_time, group_id) "
            "VALUES (:id, :who_paid_id, :amount_cents, :currency, :category, :date_time, :group_id)"
        ),
        {
            "id": transaction_id,
            "who_paid_id": who_paid_id,
            "amount_cents": amount_cents,
            "currency": currency,
            "category": category,
            "date_time": date.today(),
            "group_id": group_id,
        },
    )
    return transaction_id

def insert_debtor_share(session, transaction_id, debtor_id, split_amount_cents):
    session.execute(
        text(
            "INSERT INTO debtor_shares (transaction_id, debtor_id, split_amount_cents) "
            "VALUES (:transaction_id, :debtor_id, :split_amount_cents)"
        ),
        {"transaction_id": transaction_id, "debtor_id": debtor_id, "split_amount_cents": split_amount_cents},
    )

def insert_debt(session, group_id, debtor_id, creditor_id, amount_cents):
    session.execute(
        text(
            "INSERT INTO debts (group_id, debtor_id, creditor_id, amount_cents) "
            "VALUES (:group_id, :debtor_id, :creditor_id, :amount_cents)"
        ),
        {"group_id": group_id, "debtor_id": debtor_id, "creditor_id": creditor_id, "amount_cents": amount_cents},
    )


def test_repository_can_retrieve_a_group_with_transactions(session):
    gr_id1 = str(uuid.uuid4())
    pr_id1 = str(uuid.uuid4())
    pr_id2 = str(uuid.uuid4())
    tr_id1 = str(uuid.uuid4())
    
    insert_group(session, gr_id1, "Trip", "EUR")
    insert_person(session, pr_id1, "Luigi")
    insert_person(session, pr_id2, "Mario")
    insert_group_person(session, gr_id1, pr_id1)
    insert_group_person(session, gr_id1, pr_id2)
    insert_transaction(session, tr_id1, who_paid_id=pr_id1, group_id=gr_id1, amount_cents=20000, category="Dinner")
    insert_debtor_share(session, tr_id1, debtor_id=pr_id1, split_amount_cents=10000)
    insert_debtor_share(session, tr_id1, debtor_id=pr_id2, split_amount_cents=10000)
    insert_debt(session, gr_id1, debtor_id=pr_id2, creditor_id=pr_id1, amount_cents=10000)
    
    repo = repository.SqlRepository(session)
    retrieved = repo.get(gr_id1)
    
    assert str(retrieved.id) == gr_id1
    assert retrieved.name == "Trip"
    assert retrieved.currency == "EUR"
    
    assert {str(p.id) for p in retrieved.persons} == {pr_id1, pr_id2}
    assert len(retrieved.transactions) == 1
    t = retrieved.transactions[0]
    assert str(t.id) == tr_id1
    assert str(t.who_paid.id) == pr_id1
    assert {str(ds.debtor.id): ds.split_amount for ds in t.debtor_shares} == {pr_id1: 100, pr_id2: 100}

    assert len(retrieved.debts) == 1
    d = list(retrieved.debts)[0]
    assert str(d.debtor.id) == pr_id2
    assert str(d.creditor.id) == pr_id1
    assert d.amount == 100

def test_updating_a_group(session):

    
    
    group1 = model.Group("group1", "EUR")
    person1 = model.Person("Luigi")
    person2 = model.Person("Mario")
    share1 = model.DebtorShare(person1, 10000)
    share2 = model.DebtorShare(person2, 10000)
    transaction1 = model.Transaction(person1, 100, "EUR", [share1, share2], "Trip", date.today())
    transaction2 = model.Transaction(person1, 100, "EUR", [share1, share2], "Trip", date.today())

    group1.add_person(person1)
    group1.add_person(person2)
    group1.add_transaction(transaction1)

    repo = repository.SqlRepository(session)
    repo.add(group1)
    session.commit()

    retrieved = repo.get(group1.id)

    assert len(retrieved.transactions) == 1
    t = retrieved.transactions[0]

    assert transaction1 in retrieved.transactions 
    assert transaction2 not in retrieved.transactions

    group1.add_transaction(transaction2)

    repo.add(group1)
    session.commit()

    retrieved = repo.get(group1.id)

    assert len(retrieved.transactions) == 2
    t = retrieved.transactions[0]

    assert transaction1 in retrieved.transactions 
    assert transaction2 in retrieved.transactions


def test_removing_a_transaction_and_updating_a_group(session):
    group1 = model.Group("group1", "EUR")
    person1 = model.Person("Luigi")
    person2 = model.Person("Mario")
    share1 = model.DebtorShare(person1, 10000)
    share2 = model.DebtorShare(person2, 10000)
    transaction1 = model.Transaction(person1, 100, "EUR", [share1, share2], "Trip", date.today())

    group1.add_person(person1)
    group1.add_person(person2)
    group1.add_transaction(transaction1)

    repo = repository.SqlRepository(session)
    repo.add(group1)
    session.commit()

    retrieved = repo.get(group1.id)

    assert len(retrieved.transactions) == 1
    t = retrieved.transactions[0]

    assert transaction1 in retrieved.transactions 

    group1.remove_transaction(transaction1)

    repo.add(group1)
    session.commit()

    retrieved = repo.get(group1.id)

    assert len(retrieved.transactions) == 0
