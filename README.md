# Guitar Flash Search (Web)

Interface web em Flask para buscar músicas do Guitar Flash, com área administrativa protegida para atualizar a lista.

## Requisitos

- Python 3.11+
- Dependências em `requirements.txt`
- Dependência para deploy: `gunicorn` (opcional, mas recomendado para produção)

## Executar localmente

```bash
pip install -r requirements.txt
copy .env.example .env
python app.py
```

Acesse: `http://localhost:5000`

## Rotas

- `/` busca pública de músicas
- `/admin/login` login administrativo
- `/admin/update` atualização da lista (rota protegida)
- `/admin/logout` sair da sessão admin

## Autenticação da área protegida

Configure no arquivo `.env` (baseado em `.env.example`):

- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `PORT` (opcional, padrão: 5000)

Requisitos de segurança para `ADMIN_PASSWORD`:

- Mínimo de 12 caracteres
- Não usar senha padrão/insegura (ex.: `admin123`)

## Deploy via GitHub

Esta aplicação está pronta para deploy em serviços que conectam com repositório GitHub (ex.: Render, Railway, Fly.io).

Configurações recomendadas:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Variáveis de ambiente:
  - `ADMIN_USERNAME`
  - `ADMIN_PASSWORD`
  - `PORT` (opcional)

Se a plataforma usar `Procfile`, já existe um arquivo com:

- `web: gunicorn app:app`
