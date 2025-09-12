import abc
import domain.model as model
from sqlalchemy.orm import Session
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
        person_rows = []
        group_person_rows = []

        for person in group.persons:
            person_rows.append({"id": str(person.id), "name": person.name})
            group_person_rows.append({"group_id": str(group.id), "person_id": str(person.id)})

        if person_rows: 
            self.session.execute(
                text("INSERT INTO persons (id, name) VALUES (:id, :name) ON CONFLICT DO NOTHING"),
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
                    "amount_in_cents": transaction.amount_in_cents,
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
                        "split_amount": share.split_amount_in_cents,
                    }
                )

        if transaction_rows:
            self.session.execute(
                text(
                    "INSERT INTO transactions (id, group_id, who_paid_id, amount_in_cents, currency, category, date_time) "
                    "VALUES (:id, :group_id, :who_paid_id, :amount_in_cents, :currency, :category, :date_time)"
                ),
                transaction_rows,
            )

        if debtor_share_rows:
            self.session.execute(
                text(
                    "INSERT INTO debtor_shares (transaction_id, debtor_id, split_amount_in_cents) "
                    "VALUES (:transaction_id, :debtor_id, :split_amount)"
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
                    "amount": debt.amount_in_cents,
                }
            )

        if debt_rows:
            self.session.execute(
                text(
                    "INSERT INTO debts (group_id, debtor_id, creditor_id, amount_in_cents) "
                    "VALUES (:group_id, :debtor_id, :creditor_id, :amount)"
                ),
                debt_rows,
            )


