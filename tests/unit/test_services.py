
from datetime import date
import adapters.repository as repository
import pytest
import domain.model as model
import service_layer.services as services


class FakeRepository(repository.AbstractRepository):
    def __init__(self, batches):
        self._groups = set(batches)

    def add(self, batch):
        self._groups.add(batch)

    def get(self, id):
        return next(g for g in self._groups if g.id == id)

    def list(self):
        return list(self._groups)

class FakeSession:
    committed = False

    def commit(self):
        self.committed = True


@pytest.fixture
def person1():
    return model.Person("luigi")

@pytest.fixture
def person2():
    return model.Person("mario")

@pytest.fixture
def person3():
    return model.Person("peach")

@pytest.fixture
def group(person1, person2):
    group = model.Group("group1", "EUR")
    group.add_person(person1)
    group.add_person(person2)
    return group

@pytest.fixture
def transaction(person1, person2):
    share1 = model.DebtorShare(person1, 10000)
    share2 = model.DebtorShare(person2, 10000)
    transaction = model.Transaction(person1, 200, "EUR", [share1, share2], "Trip", date.today())
    return transaction


def test_returns_allocation(group, transaction):
    repo = FakeRepository([group]) 
    result = services.allocate(transaction, repo, FakeSession())
    assert result == transaction.id


def test_error_for_invalid_payer(group, transaction):
    repo = FakeRepository([group])

    with pytest.raises(services.InvalidSku, match="Invalid payer, person not in group"):
        services.allocate(transaction, repo, FakeSession()) 