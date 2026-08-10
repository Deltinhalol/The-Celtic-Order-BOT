# The Celtic Order BOT

Bot de Discord feito para gerenciar e dar suporte ao servidor **The Celtic Order**, reunindo funções de moderação, utilidades e comandos gerais em um só lugar.

## ✨ Funcionalidades

- 🛡️ **Moderação** — comandos para manter a ordem no servidor (kick, ban, mute, warn, etc.)
- ⚙️ **Comandos utilitários** — ferramentas do dia a dia pra facilitar a administração
- 🎉 **Comandos gerais** — interações e funções extras pra galera do servidor

> Sinta-se livre para editar essa lista com os comandos reais do bot conforme for adicionando novas funções.

## 🚀 Como rodar o bot

### Pré-requisitos

- [Python 3.10+](https://www.python.org/downloads/)
- Uma conta de bot criada no [Discord Developer Portal](https://discord.com/developers/applications)

### Instalação

1. Clone o repositório:
   \`\`\`bash
   git clone https://github.com/Deltinhalol/The-Celtic-Order-BOT.git
   cd The-Celtic-Order-BOT
   \`\`\`

2. Instale as dependências:
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

3. Copie o arquivo de exemplo de variáveis de ambiente e preencha com seus dados:
   \`\`\`bash
   cp env.example .env
   \`\`\`

4. Abra o `.env` e adicione o token do seu bot e demais configurações necessárias:
   \`\`\`
   DISCORD_TOKEN=seu_token_aqui
   \`\`\`

5. Rode o bot:
   \`\`\`bash
   python bot.py
   \`\`\`

## 📁 Estrutura do projeto

\`\`\`
The-Celtic-Order-BOT/
├── bot.py           # Arquivo principal do bot
├── env.example       # Modelo das variáveis de ambiente
├── .gitignore         # Arquivos ignorados pelo Git
└── README.md          # Este arquivo
\`\`\`

## ⚠️ Aviso de segurança

Nunca compartilhe seu arquivo `.env` ou o token do bot publicamente. O `.gitignore` já está configurado para impedir que esse arquivo seja enviado ao repositório — mantenha assim.

## 📄 Licença

Este projeto é de uso pessoal para o servidor The Celtic Order.
