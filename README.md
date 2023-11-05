# O potencial empreendedor dos bolões de apostas coletivas: uma solução de software para a modalidade pouco explorada no Brasil

## Tema

O surgimento de bancas e sites de apostas esportivas movimentou milhões nos últimos anos e se tornou um grande empreendimento no Brasil. Essas apostas são baseadas em cálculos matemáticos que calculam a probabilidade de resultados e geram uma cotação, utilizada para determinar os possíveis retornos das apostas. Os bolões e apostas coletivas também são práticas comuns há muito tempo, nas quais grupos se unem para aumentar as chances de vitória. Nesta perspectiva, este projeto busca investigar uma modalidade pouco explorada até o momento, os bolões com retorno proveniente de arrecadação coletiva.

## Problema

O grande desafio deste projeto é responder à seguinte indagação: será possível desenvolver uma solução de software viável e lucrativa, que apresente boa usabilidade e seja capaz de engajar o público, explorando o mercado mencionado anteriormente.

## Objetivos

O objetivo deste projeto é desenvolver um software capaz de cadastrar usuários que, por sua vez, poderão criar ou participar de bolões. Cada usuário terá sua própria carteira com saldo, possibilitando-o a cadastrar-se em bolões e inserir seus bilhetes. Ao cadastrar um bolão, haverá duas modalidades de escolha: resultado simples (casa, fora, empate) ou placar exato (casa ≥ 0 ≤ fora). O bolão poderá também incluir um ou mais jogos.

## Justificativa

As apostas esportivas têm ganhado cada vez mais espaço no mercado mundial, com um crescimento constante nos últimos anos. Segundo a Grand View Research, a receita global do mercado de apostas esportivas atingiu US $63,5 bilhões em 2022. No Brasil, essa modalidade de jogo tem sido regulamentada nos últimos anos e a expectativa é que esse mercado cresça consideravelmente nos próximos anos.

No entanto, mesmo com o crescente interesse do público nesse mercado, ainda há nichos pouco explorados, como é o caso das apostas esportivas via bolões. Essa prática é comum entre amigos, familiares e colegas de trabalho, que se juntam para apostar em resultados de jogos de futebol e outros esportes. Contudo, nem sempre é fácil organizar e gerenciar esses bolões, o que acaba limitando o potencial de crescimento desse mercado.

Uma das principais dificuldades dos bolões é a gestão dos bilhetes e pagamentos, além de garantir a transparência e a segurança nas transações financeiras. Para atender a essa demanda, empresas especializadas em apostas esportivas têm investido em soluções tecnológicas que facilitam a organização e administração dos bolões, tornando a prática mais acessível e segura.

Assim, é possível perceber que o mercado de apostas esportivas é bastante amplo e vem se transformando com o avanço da tecnologia e da regulamentação. Ainda há muito a ser explorado, especialmente nos nichos pouco desenvolvidos, como os bolões entre amigos e conhecidos. Com soluções inovadoras e acessíveis, é possível democratizar o acesso.

## Para instalar e rodar o projeto Django baseado nas configurações fornecidas, siga os passos abaixo

1. Certifique-se de ter o Python 3.x instalado em seu computador. Se ainda não o fez, baixe-o e instale-o em <https://www.python.org/downloads/>.
2. Abra um terminal e crie um ambiente virtual para o projeto com o comando python3 -m venv nome_do_ambiente. Substitua "nome_do_ambiente" pelo nome que desejar.
3. Ative o ambiente virtual recém-criado com o comando source nome_do_ambiente/bin/activate.
4. Navegue para o diretório onde deseja criar o projeto Django. Por exemplo, cd /home/usuario/meu_projeto.
5. Instale o Django e as dependências do projeto com o comando pip install django djangorestframework psycopg2-binary.
6. Crie um novo projeto Django com o comando django-admin startproject nome_do_projeto. Substitua "nome_do_projeto" pelo nome que desejar.
7. Navegue para o diretório do projeto recém-criado com o comando cd nome_do_projeto.
8. Crie um arquivo .env na raiz do projeto e adicione as variáveis de ambiente correspondentes às credenciais do banco de dados PostgreSQL. Por exemplo:

    ```makefile
    DB_NAME=nome_do_banco
    DB_USER=nome_do_usuario
    DB_PASSWORD=senha_do_usuario
    DB_HOST=endereco_do_servidor
    SECRET_KEY=uma_super_senha_django
    DEBUG=True
    ```

9. Rode o comando abaixo para configurar as variáveis de ambiente.

    ```bash
    export $(egrep -v '^#' .env | xargs)
    ```

10. Rode as migrações para criar as tabelas do banco de dados com o comando:

    ```bash
    python manage.py migrate
    ```

11. Crie um usuário administrador para o projeto com o comando:

    ```bash
    python manage.py createsuperuser
    ```

12. Rode o servidor de desenvolvimento

    ```bash
    python manage.py runserver
    ```

### Para renovar o certificado SSL

Parar os serviços ativos (Só o nginx já funciona):
docker-compose -f docker-compose.prod.yml stop
certbot certonly --standalone -d starbet.space
