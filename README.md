# Controle de Ponto

Sistema para integração e consulta de dados de ponto eletrônico via API Tangerino.

## Funcionalidades

- Consulta de colaboradores cadastrados
- Consulta de registros de ponto por período
- Consulta de feriados entre datas
- Integração segura via token de API

## Requisitos

- Python 3.8+
- Conta e token de acesso à API Tangerino

## Instalação

1. Clone este repositório:

   ```sh
   git clone https://github.com/seu-usuario/controle-de-ponto.git
   cd controle-de-ponto
   ```

2. Crie um ambiente virtual (opcional, mas recomendado):

   ```sh
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. Instale as dependências:

   ```sh
   pip install -r requirements.txt
   ```

## Uso

Execute o script principal conforme sua necessidade. Exemplo:

```sh
python main.py
```

## Estrutura do Projeto

```
controle-de-ponto/
│
├── api/
│   └── api.py
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Segurança

**Nunca compartilhe seu arquivo `.env` ou tokens de acesso.**  
Utilize o arquivo `.env.example` como modelo para distribuição.

## Licença

Este projeto está licenciado sob a [MIT License](LICENSE).
