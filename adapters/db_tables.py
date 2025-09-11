from sqlalchemy import Table, MetaData, Column, Integer, String, Date, ForeignKey, CHAR
import uuid

metadata = MetaData()


persons = Table(
    "persons",
    metadata,
    Column("id", CHAR(36), primary_key=True, default=uuid.uuid4),
    Column("name", String(255), nullable = False)
)

groups = Table(
    "groups",
    metadata,
    Column("id", CHAR(36), primary_key=True, default=uuid.uuid4),
    Column("name", String(255), nullable = False),
    Column("currency", String(3), nullable = False)
)

transactions = Table(
    "transactions",
    metadata,
    Column("id", CHAR(36), primary_key=True, default=uuid.uuid4),
    Column("group_id", ForeignKey("groups.id")),
    Column("who_paid_id", ForeignKey("persons.id")), 
    Column("amount_in_cents", Integer, nullable=False),
    Column("currency", String(3), nullable=False),
    Column("category", String(255), nullable=False),
    Column("date_time", Date, nullable=False),
)

debtor_shares = Table(
    "debtor_shares",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("transaction_id", ForeignKey("transactions.id")),
    Column("debtor_id", ForeignKey("persons.id")),
    Column("split_amount_in_cents", Integer, nullable=False),
)

group_persons = Table(
    "group_persons",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("group_id", ForeignKey("groups.id")),
    Column("person_id", ForeignKey("persons.id"))
)

debts = Table(
    "debts",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("group_id", ForeignKey("groups.id")),
    Column("debtor_id", ForeignKey("persons.id")),
    Column("creditor_id", ForeignKey("persons.id")),
    Column("amount_in_cents", Integer, nullable=False),
)
