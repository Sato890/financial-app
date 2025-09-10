from typing import Optional
import uuid

class Person:
    def __init__(self, name: str, id: Optional[str] = None):
        self.name = name
        self.id = id or uuid.uuid4()

    def __eq__(self, other):
        if not isinstance(other, Person):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)
    
    def __repr__(self):
        return f"Person(name={self.name})"
    
    def __str__(self):
        return self.name
    

class Group:
    def __init__(self, name: str, id: Optional[str] = None):
        self.id = id or uuid.uuid4()
        self.name = name
        self.persons = set()            

    def add_person(self, person: Person): 
        self.persons.add(person)

    def remove_person(self, person: Person): 
        self.persons.remove(person)