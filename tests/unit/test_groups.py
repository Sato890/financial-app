from domain.model import *

def test_can_add_person_in_group():
    group = Group("group1", "EUR")

    person1 = Person("luigi")
    person2 = Person("mario")

    group.add_person(person1)
    group.add_person(person2)

    assert person1 in group.persons  
    assert person2 in group.persons  

def test_can_remove_person_from_group():
    group = Group("group1", "EUR")

    person1 = Person("Luigi")
    person2 = Person("Mario")

    group.add_person(person1)
    group.add_person(person2)
    group.remove_person(person2)

    assert person1 in group.persons  
    assert person2 not in group.persons

def test_rename_person():

    person = Person("old_name")

    person.name = "new_name"
    assert person.name == "new_name"