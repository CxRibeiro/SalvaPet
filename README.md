# 🐾 Salva Pet — Resgate, localização e adoção de animais

> Aplicação interativa desenvolvida para o desafio de hackathon **Resgate de PETs ou Segurança Pública**. O sistema reúne busca de animais perdidos, registros de animais encontrados, encaminhamento para adoção e análise visual de dados.

## Apresentação do projeto

O **Salva Pet** conecta duas funcionalidades: **PetFinder**, para localizar animais perdidos e encontrados, e **AdotaPet**, para consultar animais disponíveis para adoção. A integração permite registrar um animal encontrado, verificar possíveis correspondências com registros de perdidos e, caso não seja identificado um tutor e o encaminhamento seja apropriado, disponibilizar o animal para adoção.

Esta versão está configurada para registros e consultas referentes à **cidade de São Paulo (SP)**. Trata-se de um protótipo de hackathon, não de um canal oficial de resgate ou denúncia.

## O problema

Cadastros de animais perdidos, encontrados e disponíveis para adoção podem ficar dispersos. Isso dificulta a busca por tutores, a organização de encaminhamentos e o acompanhamento dos resultados por ONGs e protetores.

## A solução

- **PetFinder:** mapa interativo de animais perdidos e encontrados, com marcadores por localização aproximada e agrupamento de pontos.
- **AdotaPet:** catálogo para consultar animais disponíveis e registrar sua adoção.
- **Cadastro:** formulário para registrar animais, suas características, bairro, situação, contatos e fotografia.
- **Integração:** pesquisa por possíveis tutores, registro de reencontros e encaminhamento para adoção responsável.
- **Dashboard:** indicadores por situação, gráficos por espécie e bairro, evolução temporal, tabela de registros e exportação CSV.
- **Autenticação:** acesso com dois perfis, conforme as funcionalidades permitidas a cada tipo de conta.

## Quem pode utilizar

- **Pessoas físicas (CPF):** acesso à página inicial, ao mapa de perdidos/encontrados e ao catálogo de adoção.
- **ONGs e petshops (CNPJ):** acesso às funções de cadastro, integração e dashboard, além das consultas disponíveis às pessoas físicas.

**Nota:** o cadastro de CNPJ atual verifica o formato de 14 dígitos; não consulta uma base oficial para atestar existência, situação cadastral ou titularidade da organização.

## Como funciona

1. O usuário cria uma conta ou entra no sistema.
2. Uma ONG ou petshop cadastra um animal como perdido, encontrado ou disponível para adoção e informa o bairro.
3. O **PetFinder** exibe registros no mapa, com pontos aproximados dos bairros configurados.
4. Na **Integração**, podem ser avaliadas possíveis correspondências entre encontrados e perdidos.
5. Havendo reencontro, o registro é atualizado. Quando não há tutor identificado e o encaminhamento é adequado, o animal pode entrar no catálogo de adoção.
6. O **Dashboard** consolida informações e permite baixar uma tabela em CSV.

O mapa **não mostra a localização exata** de um animal: os bairros cadastrados possuem coordenadas aproximadas. A opção de bairro digitado manualmente pode aparecer nas listagens sem marcador no mapa.

## Dados e transparência

- **SQLite (`petconnect.db`):** guarda usuários, abrigos, animais e histórico de movimentações.
- **`uploads/`:** guarda fotografias enviadas pelo aplicativo.
- **`assets/exemplos/`:** reúne imagens e documentação dos exemplos.
- **Localização:** utiliza uma relação de bairros e pontos de referência definida em `utils/localizacao.py`, com fonte indicada no próprio arquivo.
- **Cadastros demonstrativos:** o código contém uma rotina de dados iniciais de exemplo, quando o banco ainda não tem animais.

## Tecnologias utilizadas

| Tecnologia | Função |
| --- | --- |
| Python | Lógica da aplicação |
| Streamlit | Interface web e navegação |
| SQLite | Armazenamento local dos registros |
| Folium / streamlit-folium | Mapa interativo |
| Pandas | Tratamento e análise dos registros |
| Plotly | Gráficos e indicadores |

## Como executar localmente

**Pré-requisitos:** Python 3.10 ou superior (recomendado conferir a compatibilidade das versões instaladas) e `pip`.

1. Abra um terminal dentro da pasta `SalvaPet`.
2. Crie um ambiente virtual:

```powershell
python -m venv .venv
```

3. Ative o ambiente virtual no Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

No Linux ou macOS, use `source .venv/bin/activate`.

4. Instale as dependências:

```powershell
python -m pip install -r requirements.txt
```

5. Execute o aplicativo:

```powershell
python -m streamlit run app.py
```

6. Acesse **http://localhost:8501** no navegador.

O arquivo `petconnect.db`, se estiver presente, será utilizado; se não existir, o código inicializa um novo banco na primeira execução. As imagens relacionadas aos cadastros precisam permanecer nos caminhos esperados pelo projeto.

## Estrutura do projeto

```text
SalvaPet/
├── app.py                   # Entrada, autenticação e navegação
├── requirements.txt         # Dependências do Python
├── README.md                # Documentação do projeto
├── .gitignore               # Padrões de arquivos ignorados
├── .streamlit/
│   └── config.toml          # Configurações do Streamlit
├── petconnect.db            # Banco de dados SQLite local
├── uploads/                 # Fotos enviadas
├── assets/exemplos/         # Imagens ilustrativas
├── database/
│   └── db.py                # Tabelas, conexão e dados iniciais
├── services/
│   ├── auth.py              # Cadastro, autenticação e níveis
│   └── animals.py           # Operações com animais e fotografias
├── pages_app/
│   ├── login.py
│   ├── petfinder.py
│   ├── adotapet.py
│   ├── cadastro.py
│   ├── integracao.py
│   └── dashboard.py
├── utils/                   # Localização, formatação e constantes
└── tests/                   # Testes do projeto
```

## Requisitos do desafio atendidos

O desafio apresentado solicitava uma ferramenta de dados ou visualização focada em **resgate de pets ou segurança pública**, com código Python funcional, apresentação da solução, README curto explicando o grupo, a criação, o público e o uso, e avaliação de **insight da solução, execução técnica e comunicação**.

O Salva Pet responde à proposta com um aplicativo interativo, mapa, cadastros, indicadores, gráficos e fluxo de localização/adoção. O código e este README compõem parte do material de entrega; **o pitch e a submissão no formulário são itens separados** e não são gerados automaticamente pelo projeto.

## Equipe

- Cauã Ribeiro
- Izabelle Marrie Amaral Santos
- Pedro Caua trindade nascimento
- Caio Vitor Lizardo Avelar Agustini

