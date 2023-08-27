import factory
from faker import Faker
from monitoring.models import Transaction, User

fake = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: "person{}@example.com".format(n))
    password = factory.PostGenerationMethodCall("set_password", "passer@@@111")
    is_active = True
    firstname = fake.first_name()


class TransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Transaction

    amount = 900.00
    is_flagged = False
