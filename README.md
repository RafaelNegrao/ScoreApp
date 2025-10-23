# Score App - Tauri

Aplicativo desktop desenvolvido com Tauri, React e TypeScript.

## 🚀 Estrutura do Projeto

- **Tela de Login**: Autenticação de usuário
- **Tela Principal**: Dashboard com menu lateral navegável
  - 🏠 Home
  - 📊 Score
  - 📈 Timeline
  - ⚠️ Risks
  - ✉️ Email
  - ⚙️ Settings

## 📋 Pré-requisitos

- Node.js (v16 ou superior)
- Rust (para compilar o Tauri)
- npm ou yarn

## 🔧 Instalação

1. Instale as dependências:
```bash
npm install
```

2. Execute em modo de desenvolvimento:
```bash
npm run tauri dev
```

3. Compile para produção:
```bash
npm run tauri build
```

## 🏗️ Tecnologias

- **Tauri**: Framework para aplicativos desktop
- **React**: Biblioteca para construção de interfaces
- **TypeScript**: Superset JavaScript com tipagem estática
- **React Router**: Gerenciamento de rotas
- **Vite**: Build tool e dev server

## 📁 Estrutura de Pastas

```
Score App/
├── src/
│   ├── components/
│   │   └── MainLayout.tsx
│   ├── pages/
│   │   ├── Login.tsx
│   │   ├── Home.tsx
│   │   ├── Score.tsx
│   │   ├── Timeline.tsx
│   │   ├── Risks.tsx
│   │   ├── Email.tsx
│   │   └── Settings.tsx
│   ├── App.tsx
│   └── main.tsx
├── src-tauri/
│   └── src/
│       └── main.rs
└── package.json
```

## 🎨 Design Principles

O projeto segue os princípios de Orientação a Objetos (SOLID) e mantém:
- Código limpo e legível
- Componentes com responsabilidade única
- Nomenclatura descritiva
- Separação de concerns
