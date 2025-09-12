import abc
from typing import Optional
import uuid
import domain.model as model
from sqlalchemy import text
from sqlalchemy.engine import Connection

class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, group: model.Group):
        raise NotImplementedError
    
    @abc.abstractmethod
    def get(self, group_id: uuid.UUID) -> Optional[model.Group]:
        raise NotImplementedError


class SqlRepository(AbstractRepository):
    def __init__(self, session: Connection):
        self.session = session

    def add(self, group: model.Group):
        self._insert_group(group)
        self._insert_person_links(group)
        self._insert_transactions(group)
        self._insert_debts(group)

    def get(self, group_id: uuid.UUID) -> Optional[model.Group]:
        group_row = self._get_group_row(group_id)
        if not group_row:
            return None
        
        group = model.Group(name=group_row.name, currency=group_row.currency, id=uuid.UUID(group_row.id))
        group.persons = self._get_persons_for_group(group_id)
        group.transactions = self._get_transactions_for_group(group_id, group.persons)
        group.debts = self._get_debts_for_group(group_id, group.persons)
        
        return group
    
    def _get_group_row(self, group_id: uuid.UUID):
        return self.session.execute(
            text("SELECT id, name, currency FROM groups WHERE id = :id"),
            {"id": str(group_id)},
        ).one_or_none()

    def _get_persons_for_group(self, group_id: uuid.UUID):
        persons_rows = self.session.execute(
            text(
                "SELECT p.id, p.name FROM persons p JOIN group_persons gp ON p.id = gp.person_id WHERE gp.group_id = :group_id"
            ),
            {"group_id": str(group_id)},
        ).all()
        return [model.Person(name=row.name, id=uuid.UUID(row.id)) for row in persons_rows]

    def _get_transactions_for_group(self, group_id: uuid.UUID, persons: set):
        transactions_rows = self.session.execute(
            text("SELECT id, who_paid_id, amount_cents, currency, category, date_time FROM transactions WHERE group_id = :group_id"),
            {"group_id": str(group_id)},
        ).all()

        shares_rows = self.session.execute(
            text(
                "SELECT ds.transaction_id, ds.debtor_id, ds.split_amount_cents FROM debtor_shares ds "
                "JOIN transactions t ON ds.transaction_id = t.id "
                "WHERE t.group_id = :group_id"
            ),
            {"group_id": str(group_id)},
        ).all()

        shares_by_transaction = {}
        for s_row in shares_rows:
            if s_row.transaction_id not in shares_by_transaction:
                shares_by_transaction[s_row.transaction_id] = []
            shares_by_transaction[s_row.transaction_id].append(s_row)

        persons_by_id = {str(p.id): p for p in persons}

        transactions = []
        for t_row in transactions_rows:
            who_paid = persons_by_id.get(t_row.who_paid_id)

            shares = []
            for s_row in shares_by_transaction.get(t_row.id, []):
                debtor = persons_by_id.get(s_row.debtor_id)
                shares.append(model.DebtorShare(debtor, s_row.split_amount_cents))

            transactions.append(
                model.Transaction(
                    who_paid=who_paid,
                    amount=t_row.amount_cents,
                    currency=t_row.currency,
                    debtor_shares=shares,
                    category=t_row.category,
                    date_time=t_row.date_time,
                    id=uuid.UUID(t_row.id),
                )
            )

        return transactions

    def _get_debts_for_group(self, group_id: uuid.UUID, persons: set):
        debts_rows = self.session.execute(
            text("SELECT debtor_id, creditor_id, amount_cents FROM debts WHERE group_id = :group_id"),
            {"group_id": str(group_id)},
        ).all()
        debts = set()
        for d_row in debts_rows:
            debtor = next((p for p in persons if str(p.id) == d_row.debtor_id), None)
            creditor = next((p for p in persons if str(p.id) == d_row.creditor_id), None)
            debts.add(model.Debt(debtor, creditor, d_row.amount_cents))
        return debts

    

    def _insert_group(self, group: model.Group):
        self.session.execute(
        text(
            "INSERT INTO groups (id, name, currency) VALUES (:id, :name, :currency)"
        ),
        {"id": str(group.id), "name": group.name, "currency": group.currency},
    )
        
    def _insert_person_links(self, group: model.Group):
        person_rows = []
        group_person_rows = []

        for person in group.persons:
            person_rows.append({"id": str(person.id), "name": person.name})
            group_person_rows.append({"group_id": str(group.id), "person_id": str(person.id)})

        if person_rows: 
            self.session.execute(
                text("INSERT INTO persons (id, name) VALUES (:id, :name)"),
                person_rows,
            )

        if group_person_rows:
            self.session.execute(
                text("INSERT INTO group_persons (group_id, person_id) VALUES (:group_id, :person_id)"),
                group_person_rows,
            )

    def _insert_transactions(self, group: model.Group):
        transaction_rows = []
        debtor_share_rows = []

        for transaction in group.transactions:
            transaction_rows.append(
                {
                    "id": str(transaction.id),
                    "group_id": str(group.id),
                    "who_paid_id": str(transaction.who_paid.id),
                    "amount_cents": transaction.amount_cents,
                    "currency": transaction.currency,
                    "category": transaction.category,
                    "date_time": transaction.date_time,
                }
            )

            for share in transaction.debtor_shares:
                debtor_share_rows.append(
                    {
                        "transaction_id": str(transaction.id),
                        "debtor_id": str(share.debtor.id),
                        "split_amount_cents": share.split_amount_cents,
                    }
                )

        if transaction_rows:
            self.session.execute(
                text(
                    "INSERT INTO transactions (id, group_id, who_paid_id, amount_cents, currency, category, date_time) "
                    "VALUES (:id, :group_id, :who_paid_id, :amount_cents, :currency, :category, :date_time)"
                ),
                transaction_rows,
            )

        if debtor_share_rows:
            self.session.execute(
                text(
                    "INSERT INTO debtor_shares (transaction_id, debtor_id, split_amount_cents) "
                    "VALUES (:transaction_id, :debtor_id, :split_amount_cents)"
                ),
                debtor_share_rows,
            )

    def _insert_debts(self, group: model.Group):
        debt_rows = []

        for debt in group.debts:
            debt_rows.append(
                {
                    "group_id": str(group.id),
                    "debtor_id": str(debt.debtor.id),
                    "creditor_id": str(debt.creditor.id),
                    "amount_cents": debt.amount_cents,
                }
            )

        if debt_rows:
            self.session.execute(
                text(
                    "INSERT INTO debts (group_id, debtor_id, creditor_id, amount_cents) "
                    "VALUES (:group_id, :debtor_id, :creditor_id, :amount_cents)"
                ),
                debt_rows,
            )


