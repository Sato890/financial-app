import abc
import domain.model as model
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from sqlalchemy import text

class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, group: model.Group):
        raise NotImplementedError


class SqlRepository(AbstractRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, group: model.Group):
        self._insert_group(group)
        self._insert_person_links(group)
        self._insert_transactions(group)
        self._insert_debts(group)

    

    def _insert_group(self, group: model.Group):
        self.session.execute(
        text(
            "INSERT INTO groups (id, name, currency) VALUES (:id, :name, :currency)"
        ),
        {"id": str(group.id), "name": group.name, "currency": group.currency},
    )
        
    def _insert_person_links(self, group: model.Group):
        for person in group.persons:
            self.session.execute(
                text("INSERT INTO persons (id, name) VALUES (:id, :name) ON CONFLICT DO NOTHING"),
                {"id": str(person.id), "name": person.name},
            )
            self.session.execute(
                text("INSERT INTO group_persons (group_id, person_id) VALUES (:group_id, :person_id)"),
                {"group_id": str(group.id), "person_id": str(person.id)},
            )

    def _insert_transactions(self, group: model.Group):
        for transaction in group.transactions:
            self.session.execute(
                text(
                    "INSERT INTO transactions (id, group_id, who_paid_id, amount_in_cents, currency, category, date_time) "
                    "VALUES (:id, :group_id, :who_paid_id, :amount, :currency, :category, :date_time)"
                ),
                {
                    "id": str(transaction.id),
                    "group_id": str(group.id),
                    "who_paid_id": str(transaction.who_paid.id),
                    "amount": transaction.amount_in_cents,
                    "currency": transaction.currency,
                    "category": transaction.category,
                    "date_time": transaction.date_time,
                },
            )
            for share in transaction.debtor_shares:
                self.session.execute(
                    text(
                        "INSERT INTO debtor_shares (transaction_id, debtor_id, split_amount_in_cents) "
                        "VALUES (:transaction_id, :debtor_id, :split_amount)"
                    ),
                    {
                        "transaction_id": str(transaction.id),
                        "debtor_id": str(share.debtor.id),
                        "split_amount": share.split_amount_in_cents,
                    },
                )

    def _insert_debts(self, group: model.Group):
        for debt in group.debts:
            self.session.execute(
                text(
                    "INSERT INTO debts (group_id, debtor_id, creditor_id, amount_in_cents) "
                    "VALUES (:group_id, :debtor_id, :creditor_id, :amount)"
                ),
                {
                    "group_id": str(group.id),
                    "debtor_id": str(debt.debtor.id),
                    "creditor_id": str(debt.creditor.id),
                    "amount": debt.amount_in_cents,
                },
            )


