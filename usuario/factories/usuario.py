import factory
import pytz
from core.models import BaseModel
from usuario.models import Endereco, PermissoesNotificacao, Carteira, Usuario


class BaseModelFactory(factory.django.DjangoModelFactory):
    class Meta:
        abstract = True
        model = BaseModel

    created_at = factory.Faker("date_time_this_year", tzinfo=pytz.UTC)
    updated_at = factory.Faker("date_time_this_month", tzinfo=pytz.UTC)


class EnderecoFactory(BaseModelFactory):
    class Meta:
        model = Endereco

    cep = factory.Faker("postalcode")
    estado = factory.Faker("state")
    cidade = factory.Faker("city")
    bairro = factory.Faker("city")
    rua = factory.Faker("street_name")
    numero = factory.Faker("building_number")
    complemento = factory.Faker("sentence")


class PermissoesNotificacaoFactory(BaseModelFactory):
    class Meta:
        model = PermissoesNotificacao

    sms = True
    email = True


class CarteiraFactory(BaseModelFactory):
    class Meta:
        model = Carteira

    saldo = factory.Faker("pydecimal", left_digits=6, right_digits=2, positive=True)


class UsuarioFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Usuario

    email = factory.Faker("email")
    cpf = factory.Sequence(lambda n: f"{n:011}0")
    nome = factory.Faker("name")
    data_nascimento = factory.Faker("date_of_birth")
    telefone = '89999999999'
    endereco = factory.SubFactory(EnderecoFactory)
    permissoes = factory.SubFactory(PermissoesNotificacaoFactory)
    carteira = factory.SubFactory(CarteiraFactory)
