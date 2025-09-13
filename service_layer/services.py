import uuid
from adapters.repository import AbstractRepository
import domain.model as model

class InvalidPerson(Exception):
    pass


def are_persons_valid(transaction: model.Transaction, group: model.Group) -> bool:
    if transaction.who_paid not in group.persons:
        return False
    
    for ds in transaction.debtor_shares:
        if ds.debtor not in group.persons:
            return False
        
    return True


def add_transaction(transaction: model.Transaction, repo: AbstractRepository, session, group_id: uuid.UUID) -> model.Group:
    group = repo.get(group_id) 

    if not are_persons_valid(transaction, group): 
        raise InvalidPerson(f"Not every person is in the group")
    
    group.add_transaction(transaction)

    session.commit()
    return group
