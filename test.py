from enum import Enum


class Foo2:
    Next = None
    # Previous = Foo

    def __init__(self, v):
        self.v = v

    def p(self):
        print("Foo2", self.v)


class Foo:
    Next = Foo2

    def __init__(self, v):
        self.v = v

    def p(self):
        print("Foo", self.v)


class DynamicEnum(Enum):
    """Base class for enums that can create instances dynamically"""

    def __call__(self, *args, **kwargs):
        return self.value(*args, **kwargs)


class E(DynamicEnum):
    A = Foo
    B = Foo2


dynValue = 42
a = E.A
print(a)
print(a(12).Next)

a = a(12)
a.p()

instance_a = E.A(dynValue)  # Creates Foo(42)
instance_b = E.B(dynValue)  # Creates Foo2(42)

instance_a.p()  # Output: Foo: 42
instance_b.p()  # Output: Foo2: 42

# e.value.p()

# E.B.value.p()
