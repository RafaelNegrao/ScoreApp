# Supplier Score App

Aplicativo desktop cons## ▶️ Execução local

```powershell
cd "C:\Users\Rafael\Desktop\ScoreApp\src"## 🧰 Dicas e resolução de problemas

- **Erro de autenticação**: Verifique se o banco de dados contém usuários cadastrados. O primeiro acesso requer criação manual de usuário admin.
- **Banco bloqueado**: O modo WAL cria arquivos `db.db-wal`/`-shm`; feche o app antes de mover o banco.
- **Gráficos não aparecem**: Certifique-se de que há dados cadastrados para o fornecedor e período selecionados.
- **Exportação falha**: Verifique se o `openpyxl` está instalado (`pip install openpyxl`) e se há permissão de escrita na pasta de destino.
- **Build falhou**: Verifique se a linha de comando do PyInstaller corresponde ao caminho atual e se o ícone `.ico` existe em `images/`.on main.py
```

A aplicação iniciará com a tela de login. Após autenticação, a janela principal abrirá com as seguintes abas:

1. **Score** – Registro de scores mensais por fornecedor com todas as métricas (OTIF, NIL, Pickup, Package).
2. **Timeline** – Visualização histórica com gráficos de performance, tabela detalhada e análise estatística de tendências.
3. **Suppliers** – Gerenciamento completo do cadastro de fornecedores.
4. **Users** – Administração de usuários, permissões e privilégios (apenas para administradores).
5. **Settings** – Configurações de tema e preferências do usuário.Flet](https://flet.dev/) para gerenciamento e acompanhamento de scores de fornecedores. O projeto utiliza SQLite como persistência local e oferece um fluxo completo para registro, visualização, análise de tendências e exportação de dados com sistema de autenticação e controle de permissões.

## ✨ Principais funcionalidades

- **Sistema de autenticação**: Login com WWID e senha, com opção "Lembrar de mim" e controle de permissões por usuário.
- **Gerenciamento de fornecedores**: Cadastro completo com nome, BU, número de fornecedor e PO.
- **Registro de scores mensais**: Entrada de métricas OTIF, NIL, Quality Pickup e Quality Package com cálculo automático do Total Score.
- **Timeline de performance**: Visualização histórica com gráficos interativos, tabela detalhada e análise estatística de tendências.
- **Análise de regressão linear**: Cálculo automático de tendências, equações da reta e coeficiente R² para todas as métricas.
- **Exportação de dados**: Geração de planilhas Excel com todos os dados dos fornecedores e seus scores.
- **Temas personalizáveis**: Múltiplos temas (White, Dark, Dracula, etc.) com persistência por usuário.
- **Build nativo para Windows**: Geração de executável `.exe` via PyInstaller com ícones personalizados.

## 🛠 Arquitetura em alto nível

| Camada | Tecnologia | Observações |
| --- | --- | --- |
| Interface | Flet (Flutter + Python) | Layout responsivo, `ft.Tabs`, `ft.Card`, `ft.DataTable`, gráficos com `ft.LineChart`. |
| Regras de negócio | `main.py`, `db_manager.py` | Lógica de autenticação, cálculos de médias, regressão linear e gerenciamento de temas. |
| Persistência | SQLite (`db.db`) | Tabelas: users, suppliers, scores, themes; modo WAL ativo para concorrência. |
| Exportação | `openpyxl` | Exporta dados para planilhas Excel formatadas. |

## ✅ Pré-requisitos

- Python 3.11 ou superior (recomendado 3.13, já usado para desenvolvimento).
- `pip` atualizado.
- Sistema Windows (build do executável utiliza PyInstaller com ícones `.ico`).
- Arquivo `db.db` presente na pasta `src/` do projeto.

## 🚀 Configuração do ambiente

```powershell
# 1. (Opcional) criar ambiente virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Instalar dependências principais
pip install flet openpyxl

# 3. Dependências adicionais para empacotamento
pip install pyinstaller
```

> 💡 `openpyxl` é necessário para a funcionalidade de exportação de dados para Excel.

## ▶️ Execução local

```powershell
cd "C:\Users\Rafael\Desktop\VPCR App"
python main.py
```

A janela principal abrirá com três abas:

1. **VPCR** – Cards, filtros, painel de detalhes, TODOs e logs.
2. **Indicadores** – Resumo com métricas totais, distribuições percentuais e rankings “Top 5”.
3. **Settings** – Seleção de tema, fonte e atalhos para importação.

## 📥 Exportação de dados

1. Na aba **Suppliers**, clique no botão **Export Data**.
2. Escolha o local para salvar o arquivo Excel.
3. O sistema exportará todos os fornecedores cadastrados e seus respectivos scores históricos.
4. O arquivo gerado inclui formatação automática com cabeçalhos destacados.

## 📊 Métricas e análises disponíveis

### Aba Score
- Entrada de dados mensais com validação automática
- Cálculo automático do Total Score (média das 4 métricas)
- Histórico completo de alterações com timestamp e usuário responsável

### Aba Timeline
- **Cards de métricas**: Overall Average, 12M Average, Year Average, Q1-Q4 com indicadores de tendência
- **Gráfico de performance**: Visualização interativa com múltiplas séries (Total Score, OTIF, NIL, Pickup, Package)
- **Tabela detalhada**: Dados mensais com filtros por ano, com scroll horizontal e header fixo
- **Analytics**: Análise de regressão linear para todas as métricas com:
  - Equação da reta (y = mx + b)
  - Coeficiente de determinação (R²)
  - Classificação de tendência (Crescimento ↗, Queda ↘, Estável →)
  - Memorial de cálculo detalhado com valores observados vs preditos

Todos os componentes utilizam layout responsivo e se adaptam a diferentes resoluções de tela.

## 🗂 Estrutura do projeto

```text
ScoreApp/
├── src/
│   ├── main.py             # Lógica principal do app Flet
│   ├── db_manager.py       # Gerenciador do banco de dados SQLite
│   ├── db.db               # Banco SQLite com dados de usuários, fornecedores e scores
│   └── storage/            # Pasta para arquivos temporários e exportações
├── images/
│   └── cummins.ico         # Ícone da aplicação
├── build/                  # Artefatos gerados pelo PyInstaller
├── Supplier Score APP.exe  # Executável gerado (quando disponível)
├── comandos.txt            # Comando PyInstaller de referência
├── LICENSE                 # Licença do projeto
└── README.md               # Este arquivo
```

## 📦 Gerando o executável para Windows

Com o ambiente virtual ativado e o pacote `pyinstaller` instalado, execute na raiz do projeto:

```powershell
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
