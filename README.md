# 📦 Painel BF26 – Streamlit Web (Soma & Reserva)

Aplicação operacional para acompanhamento de pedidos, expedição e coletas, pronta para publicação web no **Streamlit Community Cloud** (ou qualquer servidor web).

---

## 🛠️ Passo 1: Criar o Ambiente Virtual Local (`venv`)

No terminal (dentro da pasta `painel_bf26`), execute:

```bash
# 1. Criação do ambiente virtual
python -m venv venv

# 2. Ativação do ambiente virtual no Windows
venv\Scripts\activate

# 3. Instalação das dependências
pip install -r requirements.txt
```

*(Ou simplesmente dê duplo clique no arquivo `preparar_ambiente_e_git.bat`)*

---

## 🐙 Passo 2: Criar o Repositório e Subir no GitHub

1. Vá até o [GitHub](https://github.com/new) e crie um novo repositório chamado **`painel-bf26`** (pode ser **Público** ou **Privado**).
2. No seu terminal, dentro da pasta `painel_bf26`, execute os comandos:

```bash
# Inicializar o git
git init

# Adicionar todos os arquivos
git add .

# Criar o primeiro commit
git commit -m "feat: Painel BF26 no Streamlit"

# Definir a branch principal como main
git branch -M main

# Vincular ao seu repositório do GitHub (troque pelo seu usuário/URL)
git remote add origin https://github.com/SEU-USUARIO/painel-bf26.git

# Enviar os arquivos
git push -u origin main
```

---

## ☁️ Passo 3: Conectar ao Serviço Web do Streamlit (Streamlit Cloud)

O **Streamlit Community Cloud** é gratuito, seguro e oficial do Streamlit:

1. Acesse **[share.streamlit.io](https://share.streamlit.io)**.
2. Faça login usando sua conta do **GitHub** (a mesma onde subiu o repositório).
3. Clique no botão azul **"Create app"** (ou **"New app"**).
4. Preencha os campos simples:
   - **Repository**: Selecione `seu-usuario/painel-bf26`
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL** (opcional): Você pode personalizar o nome do link, por exemplo: `https://painel-bf26-azzas.streamlit.app`
5. Clique em **"Deploy!"**.

Em cerca de 2 minutos sua aplicação estará **ONLINE na WEB**.

---

## 🔒 Acesso Compartilhado (SOMA e Reserva)
- Basta enviar o link gerado (ex: `https://painel-bf26-azzas.streamlit.app`) para as equipes da SOMA e da Reserva.
- O site é protegido com HTTPS automático e acessível de qualquer dispositivo (computador, celular ou tablet).
- Para alimentar a base do dia, basta entrar na aba **"📤 Gerenciar Bases / Upload"**, selecionar a planilha e clicar em salvar.
# painel-bf26
