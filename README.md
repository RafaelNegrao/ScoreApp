# 🚀 Score App

![Tauri](https://img.shields.io/badge/tauri-%23000000.svg?style=for-the-badge&logo=tauri&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)

Aplicação desktop desenvolvida como projeto de estágio para a **Cummins**. O objetivo principal foi a consolidação de notas de fornecedores para identificar gargalos e oportunidades de melhoria na logística da empresa.

---

## ✨ Funcionalidades
- Cadastro e edição de fornecedores
- Lançamento e visualização de notas por critério
- Geração automática de notas máximas
- Visualização de riscos e timeline de desempenho
- Gerenciamento de usuários e permissões
- Exportação de relatórios

---

## 🛠️ Tecnologias Utilizadas

| Frontend         | Backend         | Banco de Dados | Build/Empacotamento |
|------------------|----------------|----------------|---------------------|
| React 18         | Rust (Tauri)   | SQLite         | Vite, Tauri         |
| TypeScript       |                |                |                     |
| React Router     |                |                |                     |
| Lucide Icons     |                |                |                     |

---

## 📦 Estrutura do Projeto

```
Score App/
├── src/           # Frontend React
├── src-tauri/     # Backend Rust (Tauri)
├── database/      # Banco SQLite
├── public/        # Recursos estáticos
├── images/        # Imagens
├── package.json   # Configuração Node
└── ...
```

---

## ▶️ Como rodar localmente

1. **Instale as dependências:**
   ```bash
   npm install
   ```
2. **Execute em modo desenvolvimento:**
   ```bash
   npm run tauri dev
   ```
3. **Para gerar o executável:**
   ```bash
   npm run tauri build
   ```
   O executável será gerado em `src-tauri/target/release/score-app.exe`.

---

## 📌 Observações
- O banco de dados em produção fica na mesma pasta do executável.
- Para dúvidas ou contribuições, abra uma issue no GitHub.

---

## 👨‍💻 Autor
- [Rafael Negrão](https://github.com/RafaelNegrao)
