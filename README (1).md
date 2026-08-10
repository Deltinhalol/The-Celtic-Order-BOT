# Discord Bot

Bot de moderação/administração para Discord (comandos `$`) com um painel de comandos extra pelo terminal (`!`).

## Setup

1. Clone o repositório e entre na pasta:
   ```bash
   git clone <url-do-seu-repo>
   cd <pasta-do-repo>
   ```

2. Crie um ambiente virtual (opcional, mas recomendado):
   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/Mac
   venv\Scripts\activate      # Windows
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Copie o `.env.example` para `.env` e coloque o token real do bot:
   ```bash
   cp .env.example .env
   ```
   Edite o `.env` e substitua `coloque_seu_token_aqui` pelo token do seu bot (Discord Developer Portal).

5. Rode o bot:
   ```bash
   python bot.py
   ```

## Importante

- **Nunca** suba o arquivo `.env` pro GitHub — ele contém o token do bot. O `.gitignore` já está configurado pra ignorá-lo.
- O `backup_servidor.json` (gerado pelo comando `!backup`) também é ignorado por padrão, pois contém dados sensíveis do servidor.
- Se o token vazar por acidente, revogue-o imediatamente no Discord Developer Portal e gere um novo.

## Comandos

Veja a lista completa digitando `!help` no terminal onde o bot está rodando, ou `$help` (comandos padrão do discord.py) no chat do servidor.
