"""
Painel BF26 – Aplicação Web Streamlit (Azzas 2154 - Soma & Reserva)
Renderiza a interface idêntica ao painel original do N8N diretamente via HTML/JS,
sem dependência do SQL Server e sem travamentos de handshake de componentes.
"""

import os
import streamlit as st
import streamlit.components.v1 as components

# Configuração da página Streamlit
st.set_page_config(
    page_title="Black Friday 26 – Painel operacional",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilização CSS para ocupar 100% da tela e remover margens nativas do Streamlit
st.markdown("""
<style>
    /* Oculta barras e menus nativos do Streamlit */
    #MainMenu, header, footer, .stDeployButton { visibility: hidden !important; display: none !important; }
    div[data-testid="stToolbar"] { display: none !important; }
    .block-container { padding: 0 !important; margin: 0 !important; max-width: 100vw !important; }
    
    /* Faz o painel ocupar 100% da tela com rolagem natural */
    iframe {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        border: none !important;
        margin: 0 !important;
        padding: 0 !important;
        z-index: 999999 !important;
    }
</style>
""", unsafe_allow_html=True)

# Lê o arquivo HTML completo com o layout original do N8N
frontend_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "index.html")

if not os.path.exists(frontend_file):
    st.error("Arquivo de interface 'frontend/index.html' não encontrado.")
    st.stop()

with open(frontend_file, "r", encoding="utf-8") as f:
    html_content = f.read()

# Renderiza diretamente o HTML puro no Streamlit (carrega instantaneamente sem erro de componente)
components.html(html_content, height=1200, scrolling=True)

