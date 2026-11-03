"""
Painel BF26 – Aplicação Web Streamlit (Azzas 2154 - Soma & Reserva)
Renderiza a interface idêntica ao painel original do N8N com layout 100% fiel,
armazenamento compartilhado em disco e sem dependência do SQL Server.
"""

import os
import json
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
        z-index: 1000 !important;
    }
</style>
""", unsafe_allow_html=True)

# Diretório de armazenamento persistente no servidor
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
ORDERS_JSON = os.path.join(DATA_DIR, "saved_orders.json")
COLLS_JSON = os.path.join(DATA_DIR, "saved_colls.json")

def load_saved_data(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def save_data(filepath, data):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass

# Carrega os dados salvos previamente (compartilhados entre SOMA e Reserva)
initial_orders = load_saved_data(ORDERS_JSON)
initial_colls = load_saved_data(COLLS_JSON)

# Declaração do componente com o HTML/CSS original
frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
painel_component = components.declare_component("painel_bf26_exact", path=frontend_dir)

# Renderização do painel idêntico
event = painel_component(
    initial_orders=initial_orders,
    initial_colls=initial_colls,
    key="painel_exact_view"
)

# Se um usuário fizer upload de uma nova planilha, salva para todos
if event and isinstance(event, dict):
    ev_type = event.get("type")
    ev_data = event.get("data")
    if ev_type == "orders" and ev_data:
        save_data(ORDERS_JSON, ev_data)
    elif ev_type == "colls" and ev_data:
        save_data(COLLS_JSON, ev_data)
