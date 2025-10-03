# 📊 Supplier Score App# Supplier Score App# Supplier Score App



Sistema desktop para gerenciamento e acompanhamento de scores de fornecedores, desenvolvido com [Flet](https://flet.dev/) e SQLite.



---Aplicativo desktop construído com [Flet](https://flet.dev/) para gerenciamento e acompanhamento de scores de fornecedores. O projeto utiliza SQLite como persistência local e oferece um fluxo completo para registro, visualização, análise de tendências e exportação de dados com sistema de autenticação e controle de permissões.Aplicativo desktop cons## ▶️ Execução local



## 📋 Índice



- [Sobre](#sobre)## ✨ Principais funcionalidades```powershell

- [Funcionalidades](#funcionalidades)

- [Tecnologias](#tecnologias)cd "C:\Users\Rafael\Desktop\ScoreApp\src"## 🧰 Dicas e resolução de problemas

- [Pré-requisitos](#pré-requisitos)

- [Instalação](#instalação)- **Sistema de autenticação**: Login com WWID e senha, com opção "Lembrar de mim" e controle de permissões por usuário.

- [Como Usar](#como-usar)

- [Estrutura do Projeto](#estrutura-do-projeto)- **Gerenciamento de fornecedores**: Cadastro completo com nome, BU, número de fornecedor e PO.- **Erro de autenticação**: Verifique se o banco de dados contém usuários cadastrados. O primeiro acesso requer criação manual de usuário admin.

- [Build do Executável](#build-do-executável)

- [Troubleshooting](#troubleshooting)- **Registro de scores mensais**: Entrada de métricas OTIF, NIL, Quality Pickup e Quality Package com cálculo automático do Total Score.- **Banco bloqueado**: O modo WAL cria arquivos `db.db-wal`/`-shm`; feche o app antes de mover o banco.

- [Licença](#licença)

- **Timeline de performance**: Visualização histórica com gráficos interativos, tabela detalhada e análise estatística de tendências.- **Gráficos não aparecem**: Certifique-se de que há dados cadastrados para o fornecedor e período selecionados.

---

- **Análise de regressão linear**: Cálculo automático de tendências, equações da reta e coeficiente R² para todas as métricas.- **Exportação falha**: Verifique se o `openpyxl` está instalado (`pip install openpyxl`) e se há permissão de escrita na pasta de destino.

## 📖 Sobre

- **Exportação de dados**: Geração de planilhas Excel com todos os dados dos fornecedores e seus scores.- **Build falhou**: Verifique se a linha de comando do PyInstaller corresponde ao caminho atual e se o ícone `.ico` existe em `images/`.on main.py

O **Supplier Score App** é uma aplicação desktop completa para gerenciamento de fornecedores e seus scores de performance. O sistema oferece autenticação de usuários, registro de métricas mensais, análises estatísticas avançadas com regressão linear, visualizações gráficas interativas e exportação de dados para Excel.

- **Temas personalizáveis**: Múltiplos temas (White, Dark, Dracula, etc.) com persistência por usuário.```

---

- **Build nativo para Windows**: Geração de executável `.exe` via PyInstaller com ícones personalizados.

## ✨ Funcionalidades

A aplicação iniciará com a tela de login. Após autenticação, a janela principal abrirá com as seguintes abas:

### 🔐 Autenticação e Controle de Acesso

- Login com WWID e senha## 🛠 Arquitetura em alto nível

- Opção "Lembrar de mim"

- Controle de permissões por usuário1. **Score** – Registro de scores mensais por fornecedor com todas as métricas (OTIF, NIL, Pickup, Package).

- Gerenciamento de usuários (apenas administradores)

| Camada | Tecnologia | Observações |2. **Timeline** – Visualização histórica com gráficos de performance, tabela detalhada e análise estatística de tendências.

### 📦 Gerenciamento de Fornecedores

- Cadastro completo (nome, BU, número de fornecedor, PO)| --- | --- | --- |3. **Suppliers** – Gerenciamento completo do cadastro de fornecedores.

- Edição e exclusão de registros

- Busca e filtros| Interface | Flet (Flutter + Python) | Layout responsivo, `ft.Tabs`, `ft.Card`, `ft.DataTable`, gráficos com `ft.LineChart`. |4. **Users** – Administração de usuários, permissões e privilégios (apenas para administradores).



### 📈 Registro de Scores| Regras de negócio | `main.py`, `db_manager.py` | Lógica de autenticação, cálculos de médias, regressão linear e gerenciamento de temas. |5. **Settings** – Configurações de tema e preferências do usuário.Flet](https://flet.dev/) para gerenciamento e acompanhamento de scores de fornecedores. O projeto utiliza SQLite como persistência local e oferece um fluxo completo para registro, visualização, análise de tendências e exportação de dados com sistema de autenticação e controle de permissões.

- Entrada de métricas mensais:

  - **OTIF** (On-Time In-Full)| Persistência | SQLite (`db.db`) | Tabelas: users, suppliers, scores, themes; modo WAL ativo para concorrência. |

  - **NIL** (No Issues Logged)

  - **Quality Pickup**| Exportação | `openpyxl` | Exporta dados para planilhas Excel formatadas. |## ✨ Principais funcionalidades

  - **Quality Package**

- Cálculo automático do **Total Score** (média das 4 métricas)

- Histórico completo com timestamp e usuário responsável

## ✅ Pré-requisitos- **Sistema de autenticação**: Login com WWID e senha, com opção "Lembrar de mim" e controle de permissões por usuário.

### 📊 Timeline de Performance

- **Cards de métricas**: Overall Average, 12M Average, Year Average, Q1-Q4- **Gerenciamento de fornecedores**: Cadastro completo com nome, BU, número de fornecedor e PO.

- **Indicadores de tendência**: ↗ Crescimento, ↘ Queda, → Estável

- **Gráficos interativos**: Visualização com múltiplas séries (LineChart do Flet)- Python 3.11 ou superior (recomendado 3.13, já usado para desenvolvimento).- **Registro de scores mensais**: Entrada de métricas OTIF, NIL, Quality Pickup e Quality Package com cálculo automático do Total Score.

- **Tabela detalhada**: Dados mensais com filtros por ano

- **Analytics avançado**:- `pip` atualizado.- **Timeline de performance**: Visualização histórica com gráficos interativos, tabela detalhada e análise estatística de tendências.

  - Análise de regressão linear para todas as métricas

  - Equação da reta (y = mx + b)- Sistema Windows (build do executável utiliza PyInstaller com ícones `.ico`).- **Análise de regressão linear**: Cálculo automático de tendências, equações da reta e coeficiente R² para todas as métricas.

  - Coeficiente de determinação (R²)

  - Memorial de cálculo com valores observados vs preditos- Arquivo `db.db` presente na pasta `src/` do projeto.- **Exportação de dados**: Geração de planilhas Excel com todos os dados dos fornecedores e seus scores.



### 📥 Exportação de Dados- **Temas personalizáveis**: Múltiplos temas (White, Dark, Dracula, etc.) com persistência por usuário.

- Geração de planilhas Excel formatadas

- Exportação completa de fornecedores e histórico de scores## 🚀 Configuração do ambiente- **Build nativo para Windows**: Geração de executável `.exe` via PyInstaller com ícones personalizados.

- Formatação automática com cabeçalhos destacados



### 🎨 Personalização

- Múltiplos temas disponíveis: White, Dark, Dracula, entre outros```powershell## 🛠 Arquitetura em alto nível

- Persistência de preferências por usuário

# 1. (Opcional) criar ambiente virtual

---

python -m venv .venv| Camada | Tecnologia | Observações |

## 🛠 Tecnologias

.\.venv\Scripts\Activate.ps1| --- | --- | --- |

| Camada | Tecnologia | Descrição |

|--------|------------|-----------|| Interface | Flet (Flutter + Python) | Layout responsivo, `ft.Tabs`, `ft.Card`, `ft.DataTable`, gráficos com `ft.LineChart`. |

| **Interface** | [Flet](https://flet.dev/) | Framework Python + Flutter para apps desktop |

| **Banco de Dados** | SQLite | Persistência local com modo WAL para concorrência |# 2. Instalar dependências principais| Regras de negócio | `main.py`, `db_manager.py` | Lógica de autenticação, cálculos de médias, regressão linear e gerenciamento de temas. |

| **Gráficos** | Flet LineChart | Visualizações interativas de performance |

| **Exportação** | openpyxl | Geração de planilhas Excel |pip install flet openpyxl| Persistência | SQLite (`db.db`) | Tabelas: users, suppliers, scores, themes; modo WAL ativo para concorrência. |

| **Build** | PyInstaller | Empacotamento para executável Windows |

| Exportação | `openpyxl` | Exporta dados para planilhas Excel formatadas. |

**Estrutura do Banco de Dados:**

- `users` - Controle de autenticação e permissões# 3. Dependências adicionais para empacotamento

- `suppliers` - Cadastro de fornecedores

- `scores` - Registros mensais de métricaspip install pyinstaller## ✅ Pré-requisitos

- `themes` - Preferências de tema por usuário

```

---

- Python 3.11 ou superior (recomendado 3.13, já usado para desenvolvimento).

## ✅ Pré-requisitos

> 💡 `openpyxl` é necessário para a funcionalidade de exportação de dados para Excel.- `pip` atualizado.

- **Python 3.11+** (recomendado 3.13)

- **pip** atualizado- Sistema Windows (build do executável utiliza PyInstaller com ícones `.ico`).

- **Windows** (para build do executável)

- Arquivo `db.db` na pasta `src/`## ▶️ Execução local- Arquivo `db.db` presente na pasta `src/` do projeto.



---



## 🚀 Instalação```powershell## 🚀 Configuração do ambiente



### 1️⃣ Clone o repositóriocd "C:\Users\Rafael\Desktop\ScoreApp\src"



```powershellpython main.py```powershell

git clone https://github.com/RafaelNegrao/ScoreApp.git

cd ScoreApp```# 1. (Opcional) criar ambiente virtual

```

python -m venv .venv

### 2️⃣ (Opcional) Crie um ambiente virtual

A aplicação iniciará com a tela de login. Após autenticação, a janela principal abrirá com as seguintes abas:.\.venv\Scripts\Activate.ps1

```powershell

python -m venv .venv

.\.venv\Scripts\Activate.ps1

```1. **Score** – Registro de scores mensais por fornecedor com todas as métricas (OTIF, NIL, Pickup, Package).# 2. Instalar dependências principais



### 3️⃣ Instale as dependências2. **Timeline** – Visualização histórica com gráficos de performance, tabela detalhada e análise estatística de tendências.pip install flet openpyxl



```powershell3. **Suppliers** – Gerenciamento completo do cadastro de fornecedores.

# Dependências principais

pip install flet openpyxl4. **Users** – Administração de usuários, permissões e privilégios (apenas para administradores).# 3. Dependências adicionais para empacotamento



# Para build do executável (opcional)5. **Settings** – Configurações de tema e preferências do usuário.pip install pyinstaller

pip install pyinstaller

``````



---## 📥 Exportação de dados



## 🎯 Como Usar> 💡 `openpyxl` é necessário para a funcionalidade de exportação de dados para Excel.



### Executando a aplicação1. Na aba **Suppliers**, clique no botão **Export Data**.



```powershell2. Escolha o local para salvar o arquivo Excel.## ▶️ Execução local

cd src

python main.py3. O sistema exportará todos os fornecedores cadastrados e seus respectivos scores históricos.

```

4. O arquivo gerado inclui formatação automática com cabeçalhos destacados.```powershell

### Navegação

cd "C:\Users\Rafael\Desktop\VPCR App"

Após o login, a aplicação apresenta 5 abas principais:

## 📊 Métricas e análises disponíveispython main.py

1. **Score** 📝

   - Registro de scores mensais por fornecedor```

   - Validação automática de dados

   - Cálculo do Total Score### Aba Score



2. **Timeline** 📈- Entrada de dados mensais com validação automáticaA janela principal abrirá com três abas:

   - Visualização histórica com gráficos

   - Cards de métricas agregadas- Cálculo automático do Total Score (média das 4 métricas)

   - Análise de regressão linear

   - Tabela detalhada com filtros- Histórico completo de alterações com timestamp e usuário responsável1. **VPCR** – Cards, filtros, painel de detalhes, TODOs e logs.



3. **Suppliers** 🏭2. **Indicadores** – Resumo com métricas totais, distribuições percentuais e rankings “Top 5”.

   - CRUD completo de fornecedores

   - Exportação de dados para Excel### Aba Timeline3. **Settings** – Seleção de tema, fonte e atalhos para importação.



4. **Users** 👥- **Cards de métricas**: Overall Average, 12M Average, Year Average, Q1-Q4 com indicadores de tendência

   - Gerenciamento de usuários e permissões

   - (Apenas para administradores)- **Gráfico de performance**: Visualização interativa com múltiplas séries (Total Score, OTIF, NIL, Pickup, Package)## 📥 Exportação de dados



5. **Settings** ⚙️- **Tabela detalhada**: Dados mensais com filtros por ano, com scroll horizontal e header fixo

   - Configuração de temas

   - Preferências do usuário- **Analytics**: Análise de regressão linear para todas as métricas com:1. Na aba **Suppliers**, clique no botão **Export Data**.



### Exportando dados  - Equação da reta (y = mx + b)2. Escolha o local para salvar o arquivo Excel.



1. Acesse a aba **Suppliers**  - Coeficiente de determinação (R²)3. O sistema exportará todos os fornecedores cadastrados e seus respectivos scores históricos.

2. Clique em **Export Data**

3. Escolha o local de destino  - Classificação de tendência (Crescimento ↗, Queda ↘, Estável →)4. O arquivo gerado inclui formatação automática com cabeçalhos destacados.

4. O arquivo Excel será gerado com todos os fornecedores e histórico de scores

  - Memorial de cálculo detalhado com valores observados vs preditos

---

## 📊 Métricas e análises disponíveis

## 📁 Estrutura do Projeto

Todos os componentes utilizam layout responsivo e se adaptam a diferentes resoluções de tela.

```

ScoreApp/### Aba Score

├── src/

│   ├── main.py              # Lógica principal e interface Flet## 🗂 Estrutura do projeto- Entrada de dados mensais com validação automática

│   ├── db_manager.py        # Gerenciador do banco SQLite

│   ├── db.db                # Banco de dados (não versionado)- Cálculo automático do Total Score (média das 4 métricas)

│   └── storage/             # Arquivos temporários e exportações

│       ├── data/            # Planilhas exportadas```text- Histórico completo de alterações com timestamp e usuário responsável

│       └── temp/            # Arquivos temporários

├── images/ScoreApp/

│   └── cummins.ico          # Ícone da aplicação

├── build/                   # Artefatos do PyInstaller (gerado)├── src/### Aba Timeline

├── dist/                    # Executável final (gerado)

├── Supplier Score APP.exe   # Executável distribuível│   ├── main.py             # Lógica principal do app Flet- **Cards de métricas**: Overall Average, 12M Average, Year Average, Q1-Q4 com indicadores de tendência

├── comandos.txt             # Comandos de referência

├── LICENSE                  # Licença MIT│   ├── db_manager.py       # Gerenciador do banco de dados SQLite- **Gráfico de performance**: Visualização interativa com múltiplas séries (Total Score, OTIF, NIL, Pickup, Package)

└── README.md                # Este arquivo

```│   ├── db.db               # Banco SQLite com dados de usuários, fornecedores e scores- **Tabela detalhada**: Dados mensais com filtros por ano, com scroll horizontal e header fixo



---│   └── storage/            # Pasta para arquivos temporários e exportações- **Analytics**: Análise de regressão linear para todas as métricas com:



## 📦 Build do Executável├── images/  - Equação da reta (y = mx + b)



Para gerar o executável Windows:│   └── cummins.ico         # Ícone da aplicação  - Coeficiente de determinação (R²)



```powershell├── build/                  # Artefatos gerados pelo PyInstaller  - Classificação de tendência (Crescimento ↗, Queda ↘, Estável →)

pyinstaller --onefile --windowed --icon "images\cummins.ico" --name "Supplier Score APP" src\main.py

```├── Supplier Score APP.exe  # Executável gerado (quando disponível)  - Memorial de cálculo detalhado com valores observados vs preditos



O executável será criado em `dist\Supplier Score APP.exe`.├── comandos.txt            # Comando PyInstaller de referência



**⚠️ Importante:** Certifique-se de que o banco de dados `db.db` esteja presente na pasta `src/` antes de distribuir.├── LICENSE                 # Licença do projetoTodos os componentes utilizam layout responsivo e se adaptam a diferentes resoluções de tela.



---└── README.md               # Este arquivo



## 🧰 Troubleshooting```## 🗂 Estrutura do projeto



### ❌ Erro de autenticação

**Problema:** Não consegue fazer login  

**Solução:** Verifique se o banco de dados contém usuários cadastrados. O primeiro acesso requer criação manual de um usuário admin diretamente no banco.## 📦 Gerando o executável para Windows```text



### 🔒 Banco de dados bloqueadoScoreApp/

**Problema:** Erro ao acessar o banco  

**Solução:** O modo WAL cria arquivos `db.db-wal` e `db.db-shm`. Feche completamente a aplicação antes de mover ou copiar o banco de dados.Com o ambiente virtual ativado e o pacote `pyinstaller` instalado, execute na raiz do projeto:├── src/



### 📊 Gráficos não aparecem│   ├── main.py             # Lógica principal do app Flet

**Problema:** Timeline vazia ou sem gráficos  

**Solução:** Certifique-se de que há dados cadastrados para o fornecedor e período selecionados. Verifique se há scores registrados na aba **Score**.```powershell│   ├── db_manager.py       # Gerenciador do banco de dados SQLite



### 📥 Falha na exportaçãopyinstaller --onefile --windowed --icon "images\cummins.ico" --name "Supplier Score APP" src\main.py│   ├── db.db               # Banco SQLite com dados de usuários, fornecedores e scores

**Problema:** Erro ao exportar para Excel  

**Solução:** ```│   └── storage/            # Pasta para arquivos temporários e exportações

- Verifique se o `openpyxl` está instalado: `pip install openpyxl`

- Confirme se há permissão de escrita na pasta de destino├── images/

- Reinicie a aplicação após instalar o `openpyxl`

O executável será gerado em `dist/Supplier Score APP.exe`. Certifique-se de que o banco de dados `db.db` esteja presente na pasta `src/` antes de distribuir.│   └── cummins.ico         # Ícone da aplicação

### 🏗️ Build falhou

**Problema:** PyInstaller retorna erro  ├── build/                  # Artefatos gerados pelo PyInstaller

**Solução:** 

- Verifique se o caminho do ícone está correto: `images\cummins.ico`## 🧰 Dicas e resolução de problemas├── Supplier Score APP.exe  # Executável gerado (quando disponível)

- Certifique-se de que está executando o comando na raiz do projeto

- Verifique se o `pyinstaller` está instalado no ambiente correto├── comandos.txt            # Comando PyInstaller de referência



---- **Erro de autenticação**: Verifique se o banco de dados contém usuários cadastrados. O primeiro acesso requer criação manual de usuário admin.├── LICENSE                 # Licença do projeto



## 📄 Licença- **Banco bloqueado**: O modo WAL cria arquivos `db.db-wal`/`-shm`; feche o app antes de mover o banco.└── README.md               # Este arquivo



Este projeto está sob a licença **MIT**. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.- **Gráficos não aparecem**: Certifique-se de que há dados cadastrados para o fornecedor e período selecionados.```



---- **Exportação falha**: Verifique se o `openpyxl` está instalado (`pip install openpyxl`) e se há permissão de escrita na pasta de destino.



## 👨‍💻 Desenvolvido por- **Build falhou**: Verifique se a linha de comando do PyInstaller corresponde ao caminho atual e se o ícone `.ico` existe em `images/`.## 📦 Gerando o executável para Windows



**Rafael Negrão**  

[GitHub](https://github.com/RafaelNegrao)

## 📄 LicençaCom o ambiente virtual ativado e o pacote `pyinstaller` instalado, execute na raiz do projeto:

---



**⭐ Se este projeto foi útil, considere dar uma estrela no repositório!**

Distribuído sob a licença [MIT](LICENSE). Consulte o arquivo para detalhes.```powershell

pyinstaller --onefile --windowed --icon "images\cummins.ico" --name "Supplier Score APP" src\main.py
```

O executável será gerado em `dist/Supplier Score APP.exe`. Certifique-se de que o banco de dados `db.db` esteja presente na pasta `src/` antes de distribuir.

## 🧰 Dicas e resolução de problemas

- **Mensagem “Biblioteca openpyxl não instalada”**: rode `pip install openpyxl` e reinicie o app.
- **Banco bloqueado**: o modo WAL cria arquivos `vpcr_database.db-wal`/`-shm`; feche o app antes de mover o banco.
- **Atualização de indicadores**: use o botão de recarregar dados após importar planilhas ou editar registros diretamente no banco.
- **Build falhou**: verifique se a linha de comando do PyInstaller corresponde ao caminho atual e se os ícones `.ico` existem na raiz.

## 📄 Licença

Distribuído sob a licença [MIT](LICENSE). Consulte o arquivo para detalhes.
