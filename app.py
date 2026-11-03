"""
Painel BF26 – Painel Operacional e Monitoramento de Coletas (Streamlit)
Migrado de N8N / SQL Server para aplicação Streamlit independente.
Suporta Grupo SOMA e Reserva sem necessidade de acesso ao SQL Server.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from data_processing import (
    process_orders_dataframe,
    process_coletas_dataframe,
    canonical_brand
)
from storage import (
    save_orders_dataset,
    load_orders_dataset,
    save_coletas_dataset,
    load_coletas_dataset,
    load_metadata
)

# Configuração da Página
st.set_page_config(
    page_title="Painel BF26 – Operação e Coletas",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================================
# ESTILOS CSS CUSTOMIZADOS (Identidade visual elegante e corporativa)
# =====================================================================
st.markdown("""
<style>
    /* Estilos Gerais */
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 12px;
        position: relative;
        overflow: hidden;
    }
    .metric-card p {
        margin: 0;
        font-size: 13px;
        font-weight: 600;
        color: #64748b;
    }
    .metric-card h2 {
        margin: 8px 0 4px;
        font-size: 28px;
        font-weight: 800;
        color: #1e293b;
    }
    .metric-card .sub {
        font-size: 11px;
        color: #94a3b8;
    }
    
    /* Bordas coloridas para fluxo */
    .card-sold { border-left: 5px solid #2563eb; }
    .card-proc { border-left: 5px solid #f59e0b; }
    .card-ship { border-left: 5px solid #6366f1; }
    .card-await { border-left: 5px solid #ea580c; }
    .card-transit { border-left: 5px solid #0ea5e9; }
    .card-done { border-left: 5px solid #16a37a; }

    /* Barra de progresso visual interna */
    .progress-bar-bg {
        background-color: #f1f5f9;
        border-radius: 9999px;
        height: 6px;
        width: 100%;
        margin-top: 6px;
        overflow: hidden;
    }
    .progress-bar-fill {
        height: 100%;
        border-radius: 9999px;
    }

    /* Títulos de seção */
    .section-title {
        font-size: 13px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        margin: 20px 0 10px 0;
        border-bottom: 1px solid #e2e8f0;
        padding-bottom: 4px;
    }
    
    /* Tags de status */
    .tag-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# AUTENTICAÇÃO OPCIONAL VIA SECRETS
# =====================================================================
def check_password():
    # Se não houver 'password' nos secrets, o acesso é liberado diretamente
    if "password" not in st.secrets:
        return True

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.markdown("<br><h2 style='text-align:center;'>🔒 Painel BF26 – Acesso Seguro</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color: #64748b;'>Ambiente restrito às equipes Grupo SOMA e Reserva</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        pwd = st.text_input("Digite a senha de acesso:", type="password", key="login_pwd")
        if st.button("Entrar no Painel", type="primary", use_container_width=True):
            if pwd == st.secrets["password"]:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Senha incorreta. Tente novamente.")
    return False

if not check_password():
    st.stop()

# =====================================================================
# FUNÇÕES AUXILIARES DE FORMATAÇÃO E CACHE
# =====================================================================

def fmt_num(v):
    if v is None or pd.isna(v):
        return "—"
    return f"{int(v):,}".replace(",", ".")

def fmt_dec(v, d=1):
    if v is None or pd.isna(v):
        return "—"
    return f"{v:.{d}f}".replace(".", ",")

def fmt_pct(v):
    if v is None or pd.isna(v):
        return "—"
    return f"{v:.1f}%".replace(".", ",")

def fmt_brl(v):
    if v is None or pd.isna(v):
        return "—"
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def render_kpi_card(title, value, sub="", card_class="card-sold", progress=None, prog_color="#2563eb"):
    prog_html = ""
    if progress is not None:
        p_pct = min(100.0, max(0.0, float(progress)))
        prog_html = f"""
        <div class="progress-bar-bg">
            <div class="progress-bar-fill" style="width: {p_pct}%; background-color: {prog_color};"></div>
        </div>
        """
    st.markdown(f"""
    <div class="metric-card {card_class}">
        <p>{title}</p>
        <h2>{value}</h2>
        {prog_html}
        <div class="sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

# =====================================================================
# CARGA DE DADOS DO STORAGE PERSISTENTE
# =====================================================================

@st.cache_data(show_spinner="Carregando base de dados...")
def get_orders_data():
    return load_orders_dataset()

@st.cache_data(show_spinner="Carregando coletas...")
def get_coletas_data():
    return load_coletas_dataset()

# =====================================================================
# SIDEBAR: NAVEGAÇÃO E METADADOS
# =====================================================================

st.sidebar.markdown("### 🏢 Azzas 2154")
st.sidebar.caption("Operação Soma & Reserva – BF26")

metadata = load_metadata()
menu_option = st.sidebar.radio(
    "Navegação",
    ["📊 Painel Operacional", "🚚 Monitoramento de Coletas", "📤 Gerenciar Bases / Upload"],
    index=0
)

st.sidebar.markdown("---")

# Informações da base atual na sidebar
st.sidebar.markdown("#### ℹ️ Status das Bases")
orders_meta = metadata.get("orders")
coletas_meta = metadata.get("coletas")

if orders_meta:
    st.sidebar.markdown(f"""
    **Pedidos:**  
    📄 `{orders_meta.get('filename')}`  
    🔢 {fmt_num(orders_meta.get('rows'))} linhas  
    🕒 {orders_meta.get('updated_at')}
    """)
else:
    st.sidebar.warning("Nenhuma base de Pedidos carregada.")

if coletas_meta:
    st.sidebar.markdown(f"""
    **Coletas:**  
    📄 `{coletas_meta.get('filename')}`  
    🔢 {fmt_num(coletas_meta.get('rows'))} registros  
    🕒 {coletas_meta.get('updated_at')}
    """)
else:
    st.sidebar.info("Nenhuma base de Coletas carregada.")

if st.sidebar.button("🔄 Recarregar Dados"):
    st.cache_data.clear()
    st.rerun()

# =====================================================================
# TELA 1: GERENCIAR BASES / UPLOAD DE ARQUIVOS
# =====================================================================
if menu_option == "📤 Gerenciar Bases / Upload":
    st.title("📤 Upload e Gestão de Planilhas")
    st.write("Faça o upload das planilhas operacionais. Os dados são salvos localmente e ficam acessíveis para todos os usuários.")
    
    col_up1, col_up2 = st.columns(2)
    
    with col_up1:
        st.subheader("📦 Planilha de Pedidos")
        st.caption("Colunas principais: MARCA REAL, TRANSPORTADORA REAL, ORIGEM REAL, TIPO (BU), DATA_HORA_INTEGRACAO, UF_DESTINO, DE X PARA CORRIGIDO, etc.")
        orders_file = st.file_uploader("Arquivo de Pedidos (.xlsx, .csv)", type=["xlsx", "xlsm", "csv", "txt"], key="orders_up")
        
        if orders_file is not None:
            if st.button("Processar e Salvar Base de Pedidos", type="primary"):
                with st.spinner("Processando planilha de pedidos..."):
                    try:
                        if orders_file.name.lower().endswith((".csv", ".txt")):
                            try:
                                df_raw = pd.read_csv(orders_file, sep=";", encoding="utf-8", low_memory=False)
                            except UnicodeDecodeError:
                                orders_file.seek(0)
                                df_raw = pd.read_csv(orders_file, sep=";", encoding="latin-1", low_memory=False)
                        else:
                            df_raw = pd.read_excel(orders_file)
                        
                        df_processed = process_orders_dataframe(df_raw)
                        save_orders_dataset(df_processed, filename=orders_file.name)
                        st.cache_data.clear()
                        st.success(f"Base de Pedidos salva com sucesso! {len(df_processed):,} pedidos processados.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao processar planilha: {e}")

    with col_up2:
        st.subheader("🚚 Planilha de Coletas")
        st.caption("Colunas: Data do Pedido, Transportadora, UF Destino, Marca, Origem, Número do Pedido, Nome da Loja, Situação.")
        coletas_file = st.file_uploader("Arquivo de Coletas (.xlsx, .csv)", type=["xlsx", "xlsm", "csv", "txt"], key="coletas_up")
        
        if coletas_file is not None:
            if st.button("Processar e Salvar Base de Coletas", type="primary"):
                with st.spinner("Processando planilha de coletas..."):
                    try:
                        if coletas_file.name.lower().endswith((".csv", ".txt")):
                            try:
                                df_raw = pd.read_csv(coletas_file, sep=";", encoding="utf-8", low_memory=False)
                            except UnicodeDecodeError:
                                coletas_file.seek(0)
                                df_raw = pd.read_csv(coletas_file, sep=";", encoding="latin-1", low_memory=False)
                        else:
                            df_raw = pd.read_excel(coletas_file)
                        
                        df_processed = process_coletas_dataframe(df_raw)
                        save_coletas_dataset(df_processed, filename=coletas_file.name)
                        st.cache_data.clear()
                        st.success(f"Base de Coletas salva com sucesso! {len(df_processed):,} coletas processadas.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao processar planilha de coletas: {e}")

# =====================================================================
# TELA 2: PAINEL OPERACIONAL (PEDIDOS)
# =====================================================================
elif menu_option == "📊 Painel Operacional":
    df_orders = get_orders_data()
    
    if df_orders is None or df_orders.empty:
        st.warning("Nenhuma base de pedidos disponível. Acesse a aba '📤 Gerenciar Bases / Upload' para carregar a planilha.")
        st.stop()
    
    # ---------------- FILTROS NA SIDEBAR ----------------
    st.sidebar.markdown("### 🔍 Filtros Operacionais")
    
    # Filtro de datas
    min_date = df_orders['sold_date'].min()
    max_date = df_orders['sold_date'].max()
    
    date_range = st.sidebar.date_input(
        "Período de Venda",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # BU
    bu_options = sorted([str(x) for x in df_orders['bu'].dropna().unique()])
    sel_bu = st.sidebar.multiselect("BU (Business Unit)", options=bu_options, default=[])
    
    # Origem
    origin_options = sorted([str(x) for x in df_orders['origin'].dropna().unique()])
    sel_origin = st.sidebar.multiselect("Origem", options=origin_options, default=[])
    
    # Marca
    brand_options = sorted([str(x) for x in df_orders['brand'].dropna().unique()])
    sel_brand = st.sidebar.multiselect("Marca", options=brand_options, default=[])
    
    # Transportadora
    carrier_options = sorted([str(x) for x in df_orders['carrier'].dropna().unique()])
    sel_carrier = st.sidebar.multiselect("Transportadora", options=carrier_options, default=[])
    
    # Aplicação dos Filtros
    df_filtered = df_orders.copy()
    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        df_filtered = df_filtered[
            (df_filtered['sold_date'] >= date_range[0]) & 
            (df_filtered['sold_date'] <= date_range[1])
        ]
    elif isinstance(date_range, (tuple, list)) and len(date_range) == 1:
        df_filtered = df_filtered[df_filtered['sold_date'] == date_range[0]]
        
    if sel_bu:
        df_filtered = df_filtered[df_filtered['bu'].isin(sel_bu)]
    if sel_origin:
        df_filtered = df_filtered[df_filtered['origin'].isin(sel_origin)]
    if sel_brand:
        df_filtered = df_filtered[df_filtered['brand'].isin(sel_brand)]
    if sel_carrier:
        df_filtered = df_filtered[df_filtered['carrier'].isin(sel_carrier)]
        
    # Cabeçalho Principal
    st.title("BLACK FRIDAY 26 | Painel Operacional")
    st.caption("Acompanhamento de pedidos, expedição e nível de serviço de transporte")
    
    d_start = df_filtered['sold_date'].min().strftime('%d/%m/%Y') if not df_filtered.empty else "—"
    d_end = df_filtered['sold_date'].max().strftime('%d/%m/%Y') if not df_filtered.empty else "—"
    st.info(f"📅 **Período exibido:** {d_start} até {d_end} | **Pedidos no filtro:** {fmt_num(len(df_filtered))}")
    
    if df_filtered.empty:
        st.warning("Nenhum pedido encontrado para a combinação de filtros selecionada.")
        st.stop()
        
    # ---------------- 1. FLUXO: ONDE ESTÁ MEU PEDIDO ----------------
    st.markdown('<div class="section-title">Rastreamento de Pedidos · Onde está meu pedido</div>', unsafe_allow_html=True)
    
    total_sold = len(df_filtered)
    total_proc = len(df_filtered[df_filtered['stage'] == 'processing'])
    total_shipped = total_sold - total_proc
    
    col1, col2, col3 = st.columns(3)
    with col1:
        render_kpi_card("Vendido", fmt_num(total_sold), "Total de pedidos integrados", "card-sold", 100.0, "#2563eb")
    with col2:
        proc_pct = (total_proc / total_sold * 100) if total_sold else 0
        render_kpi_card("Em processamento", fmt_num(total_proc), f"{fmt_pct(proc_pct)} do total vendido", "card-proc", proc_pct, "#f59e0b")
    with col3:
        ship_pct = (total_shipped / total_sold * 100) if total_sold else 0
        render_kpi_card("Expedido", fmt_num(total_shipped), f"{fmt_pct(ship_pct)} do total vendido", "card-ship", ship_pct, "#6366f1")
        
    st.markdown("##### Dos pedidos expedidos:")
    total_await = len(df_filtered[df_filtered['stage'] == 'awaitingCollection'])
    total_transit = len(df_filtered[df_filtered['stage'] == 'transit'])
    total_delivered = len(df_filtered[df_filtered['stage'] == 'delivered'])
    
    col4, col5, col6 = st.columns(3)
    with col4:
        await_pct = (total_await / total_shipped * 100) if total_shipped else 0
        render_kpi_card("Aguardando coleta", fmt_num(total_await), f"{fmt_pct(await_pct)} dos expedidos", "card-await", await_pct, "#ea580c")
    with col5:
        transit_pct = (total_transit / total_shipped * 100) if total_shipped else 0
        render_kpi_card("Em trânsito", fmt_num(total_transit), f"{fmt_pct(transit_pct)} dos expedidos", "card-transit", transit_pct, "#0ea5e9")
    with col6:
        del_pct = (total_delivered / total_shipped * 100) if total_shipped else 0
        render_kpi_card("Entregue", fmt_num(total_delivered), f"{fmt_pct(del_pct)} dos expedidos", "card-done", del_pct, "#16a37a")

    # ---------------- 2. DEMANDA E ATENDIMENTO POR MARCA (DAILY LOGISTICS) ----------------
    st.markdown('<div class="section-title">Demanda e Atendimento por Marca (Daily Logistics)</div>', unsafe_allow_html=True)
    
    metric_view = st.radio(
        "Métrica exibida no gráfico:",
        ["Pedidos", "Peças", "Valor (R$)"],
        horizontal=True
    )
    
    # Agrupamento por Marca
    brand_agg = []
    for brand_name, g in df_filtered.groupby('brand'):
        integ_ped = len(g)
        proc_ped = len(g[g['stage'] == 'processing'])
        atend_ped = integ_ped - proc_ped
        
        integ_pecas = g['pieces'].sum()
        proc_pecas = g[g['stage'] == 'processing']['pieces'].sum()
        atend_pecas = integ_pecas - proc_pecas
        
        integ_val = g['value'].sum()
        proc_val = g[g['stage'] == 'processing']['value'].sum()
        atend_val = integ_val - proc_val
        
        # Lead time de despacho
        valid_dispatch = g['dispatch_lead_days'].dropna()
        avg_disp_lead = valid_dispatch.mean() if len(valid_dispatch) > 0 else np.nan
        
        # Cumprimento de SLA
        sla_rows = g['sla_met'].dropna()
        sla_pct = (sla_rows.sum() / len(sla_rows) * 100) if len(sla_rows) > 0 else np.nan
        
        brand_agg.append({
            "Marca": brand_name,
            "Integrado_Ped": integ_ped,
            "Atendido_Ped": atend_ped,
            "Pendente_Ped": proc_ped,
            "Integrado_Pecas": integ_pecas,
            "Atendido_Pecas": atend_pecas,
            "Pendente_Pecas": proc_pecas,
            "Integrado_Val": integ_val,
            "Atendido_Val": atend_val,
            "Pendente_Val": proc_val,
            "Lead_Despacho": avg_disp_lead,
            "SLA_Pct": sla_pct
        })
        
    df_brand = pd.DataFrame(brand_agg).sort_values(by="Integrado_Ped", ascending=False)
    
    if not df_brand.empty:
        if metric_view == "Peças":
            col_int, col_at = "Integrado_Pecas", "Atendido_Pecas"
            y_title = "Quantidade de Peças"
        elif metric_view == "Valor (R$)":
            col_int, col_at = "Integrado_Val", "Atendido_Val"
            y_title = "Valor Total (R$)"
        else:
            col_int, col_at = "Integrado_Ped", "Atendido_Ped"
            y_title = "Quantidade de Pedidos"
            
        fig_brand = go.Figure()
        fig_brand.add_trace(go.Bar(
            x=df_brand['Marca'],
            y=df_brand[col_int],
            name='Integrado',
            marker_color='#3b82f6'
        ))
        fig_brand.add_trace(go.Bar(
            x=df_brand['Marca'],
            y=df_brand[col_at],
            name='Atendido (Expedido)',
            marker_color='#10b981'
        ))
        fig_brand.update_layout(
            barmode='group',
            height=380,
            margin=dict(l=20, r=20, t=30, b=30),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis_title=y_title,
            hovermode="x unified"
        )
        st.plotly_chart(fig_brand, use_container_width=True)
        
        with st.expander("Ver Tabela Detalhada por Marca"):
            df_brand_display = pd.DataFrame()
            df_brand_display['Marca'] = df_brand['Marca']
            if metric_view == "Peças":
                df_brand_display['Integrado'] = df_brand['Integrado_Pecas'].apply(fmt_num)
                df_brand_display['Atendido'] = df_brand['Atendido_Pecas'].apply(fmt_num)
                df_brand_display['Pendente'] = df_brand['Pendente_Pecas'].apply(fmt_num)
            elif metric_view == "Valor (R$)":
                df_brand_display['Integrado'] = df_brand['Integrado_Val'].apply(fmt_brl)
                df_brand_display['Atendido'] = df_brand['Atendido_Val'].apply(fmt_brl)
                df_brand_display['Pendente'] = df_brand['Pendente_Val'].apply(fmt_brl)
            else:
                df_brand_display['Integrado'] = df_brand['Integrado_Ped'].apply(fmt_num)
                df_brand_display['Atendido'] = df_brand['Atendido_Ped'].apply(fmt_num)
                df_brand_display['Pendente'] = df_brand['Pendente_Ped'].apply(fmt_num)
            
            df_brand_display['Lead Time Despacho'] = df_brand['Lead_Despacho'].apply(lambda x: f"{fmt_dec(x)} d" if pd.notna(x) else "—")
            df_brand_display['SLA no Prazo'] = df_brand['SLA_Pct'].apply(fmt_pct)
            st.dataframe(df_brand_display, hide_index=True, use_container_width=True)

    # ---------------- 3. NÍVEL DE SERVIÇO E RISCOS ----------------
    st.markdown('<div class="section-title">Nível de Serviço e Riscos</div>', unsafe_allow_html=True)
    
    val_disp = df_filtered['dispatch_lead_days'].dropna()
    avg_disp_lead_total = val_disp.mean() if len(val_disp) > 0 else np.nan
    
    sla_all = df_filtered['sla_met'].dropna()
    sla_pct_total = (sla_all.sum() / len(sla_all) * 100) if len(sla_all) > 0 else np.nan
    
    backlog_overdue = df_filtered['is_overdue'].sum()
    
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
    with kpi_col1:
        st.metric("Lead time médio (despacho)", f"{fmt_dec(avg_disp_lead_total)} dias" if pd.notna(avg_disp_lead_total) else "—")
    with kpi_col2:
        st.metric("Cumprimento do SLA", fmt_pct(sla_pct_total))
    with kpi_col3:
        st.metric("Backlog acima do SLA", f"{fmt_num(backlog_overdue)} pedidos")

    # ---------------- 4. ESTRATIFICAÇÃO POR ETAPAS ----------------
    st.markdown('<div class="section-title">Estratificação por Etapas</div>', unsafe_allow_html=True)
    
    strat_type = st.radio("Estratificar por:", ["Transportadora", "UF Destino"], horizontal=True)
    strat_col = "carrier" if strat_type == "Transportadora" else "uf"
    
    strat_rows = []
    for name, g in df_filtered.groupby(strat_col):
        tot = len(g)
        proc = len(g[g['stage'] == 'processing'])
        awaiting = len(g[g['stage'] == 'awaitingCollection'])
        trans = len(g[g['stage'] == 'transit'])
        deli = len(g[g['stage'] == 'delivered'])
        rate = (deli / tot * 100) if tot else 0.0
        strat_rows.append({
            strat_type: name,
            "Em processamento": proc,
            "Aguardando coleta": awaiting,
            "Em trânsito": trans,
            "Entregue": deli,
            "Total Geral": tot,
            "Taxa de entrega": rate
        })
        
    df_strat = pd.DataFrame(strat_rows).sort_values(by="Total Geral", ascending=False)
    
    if not df_strat.empty:
        # Linha de total
        tot_row = {
            strat_type: "TOTAL GERAL",
            "Em processamento": df_strat["Em processamento"].sum(),
            "Aguardando coleta": df_strat["Aguardando coleta"].sum(),
            "Em trânsito": df_strat["Em trânsito"].sum(),
            "Entregue": df_strat["Entregue"].sum(),
            "Total Geral": df_strat["Total Geral"].sum(),
            "Taxa de entrega": (df_strat["Entregue"].sum() / df_strat["Total Geral"].sum() * 100) if df_strat["Total Geral"].sum() else 0.0
        }
        df_strat_display = pd.concat([df_strat, pd.DataFrame([tot_row])], ignore_index=True)
        
        st.dataframe(
            df_strat_display.style.format({
                "Em processamento": "{:,.0f}",
                "Aguardando coleta": "{:,.0f}",
                "Em trânsito": "{:,.0f}",
                "Entregue": "{:,.0f}",
                "Total Geral": "{:,.0f}",
                "Taxa de entrega": "{:.1f}%"
            }),
            hide_index=True,
            use_container_width=True
        )

    # ---------------- 5. SHARE POR TRANSPORTADORA ----------------
    st.markdown('<div class="section-title">Share por Transportadora</div>', unsafe_allow_html=True)
    
    carrier_agg = []
    for c_name, g in df_filtered.groupby('carrier'):
        tot = len(g)
        deli = len(g[g['stage'] == 'delivered'])
        carrier_agg.append({
            "Transportadora": c_name,
            "Pedidos": tot,
            "Share": (tot / total_sold * 100) if total_sold else 0,
            "Entregue": deli,
            "Taxa_Entrega": (deli / tot * 100) if tot else 0
        })
    df_carrier = pd.DataFrame(carrier_agg).sort_values(by="Pedidos", ascending=False)
    
    if not df_carrier.empty:
        col_c1, col_c2 = st.columns([2, 1])
        with col_c1:
            fig_sh = px.bar(
                df_carrier.head(10),
                x="Pedidos",
                y="Transportadora",
                orientation="h",
                text="Pedidos",
                color="Pedidos",
                color_continuous_scale="Blues",
                title="Top 10 Transportadoras por Volume"
            )
            fig_sh.update_layout(yaxis=dict(autorange="reversed"), height=350, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_sh, use_container_width=True)
            
        with col_c2:
            st.markdown("##### Destaques (Top 4)")
            for _, r in df_carrier.head(4).iterrows():
                st.markdown(f"""
                **{r['Transportadora']}**  
                Volume: **{fmt_num(r['Pedidos'])}** ({fmt_pct(r['Share'])}) | Entrega: **{fmt_pct(r['Taxa_Entrega'])}**
                ---
                """)

    # ---------------- 6. LEAD TIME OPERACIONAL (VENDA À ENTREGA) ----------------
    st.markdown('<div class="section-title">Lead Time Operacional (Venda à Entrega)</div>', unsafe_allow_html=True)
    
    deliv_lead_days = df_filtered['delivery_lead_days'].dropna()
    
    if len(deliv_lead_days) > 0:
        l_min = deliv_lead_days.min()
        l_avg = deliv_lead_days.mean()
        l_max = deliv_lead_days.max()
        p50 = np.percentile(deliv_lead_days, 50)
        p75 = np.percentile(deliv_lead_days, 75)
        p90 = np.percentile(deliv_lead_days, 90)
        p95 = np.percentile(deliv_lead_days, 95)
        
        m_col1, m_col2, m_col3, m_col4, m_col5, m_col6, m_col7 = st.columns(7)
        m_col1.metric("Mínimo", f"{fmt_dec(l_min)} d")
        m_col2.metric("Média", f"{fmt_dec(l_avg)} d")
        m_col3.metric("Máximo", f"{fmt_dec(l_max)} d")
        m_col4.metric("P50", f"{fmt_dec(p50)} d")
        m_col5.metric("P75", f"{fmt_dec(p75)} d")
        m_col6.metric("P90", f"{fmt_dec(p90)} d")
        m_col7.metric("P95", f"{fmt_dec(p95)} d")
        
        # Lead time por UF
        uf_lead = []
        for uf, g in df_filtered[df_filtered['delivery_lead_days'].notna()].groupby('uf'):
            uf_lead.append({
                "UF": uf,
                "Pedidos_Entregues": len(g),
                "Lead_Time_Medio": g['delivery_lead_days'].mean()
            })
        df_uf_lead = pd.DataFrame(uf_lead).sort_values(by="Lead_Time_Medio", ascending=False)
        
        fig_uf = go.Figure()
        fig_uf.add_trace(go.Bar(
            x=df_uf_lead['UF'],
            y=df_uf_lead['Pedidos_Entregues'],
            name='Pedidos Entregues',
            yaxis='y',
            marker_color='#93c5fd'
        ))
        fig_uf.add_trace(go.Scatter(
            x=df_uf_lead['UF'],
            y=df_uf_lead['Lead_Time_Medio'],
            name='Lead Time Médio (dias)',
            yaxis='y2',
            mode='lines+markers',
            marker=dict(color='#f59e0b', size=7),
            line=dict(color='#f59e0b', width=2)
        ))
        fig_uf.update_layout(
            height=380,
            margin=dict(l=20, r=20, t=30, b=30),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis=dict(title='Pedidos Entregues'),
            yaxis2=dict(title='Lead Time Médio (dias)', overlaying='y', side='right'),
            hovermode="x unified"
        )
        st.plotly_chart(fig_uf, use_container_width=True)
    else:
        st.info("Nenhuma entrega concluída encontrada no período para cálculo de Lead Time.")

    # ---------------- 7. MOVIMENTAÇÕES RECENTES ----------------
    st.markdown('<div class="section-title">Últimas Movimentações</div>', unsafe_allow_html=True)
    recent_cols = ['order_id', 'origin', 'operation', 'brand', 'carrier', 'status', 'sold_at', 'delivered_at', 'delivery_lead_days']
    df_recent = df_filtered[recent_cols].copy().sort_values(by="sold_at", ascending=False).head(20)
    df_recent.columns = ['Pedido', 'Origem', 'Operação', 'Marca', 'Transportadora', 'Status', 'Venda', 'Entrega', 'Lead Time (dias)']
    
    st.dataframe(
        df_recent.style.format({
            "Venda": lambda x: x.strftime('%d/%m/%Y %H:%M') if pd.notna(x) else "—",
            "Entrega": lambda x: x.strftime('%d/%m/%Y %H:%M') if pd.notna(x) else "—",
            "Lead Time (dias)": lambda x: f"{fmt_dec(x)} d" if pd.notna(x) else "Em andamento"
        }),
        hide_index=True,
        use_container_width=True
    )

# =====================================================================
# TELA 3: MONITORAMENTO OPERACIONAL DE COLETAS
# =====================================================================
elif menu_option == "🚚 Monitoramento de Coletas":
    df_coletas = get_coletas_data()
    
    if df_coletas is None or df_coletas.empty:
        st.warning("Nenhuma base de coletas disponível. Acesse a aba '📤 Gerenciar Bases / Upload' para carregar a planilha de coletas.")
        st.stop()
        
    st.title("Monitoramento Operacional de Coletas")
    st.caption("Acompanhamento de coletas por marca, loja e transportadora")
    
    # Filtros na sidebar para Coletas
    st.sidebar.markdown("### 🔍 Filtros de Coletas")
    
    c_min_date = df_coletas['date'].min()
    c_max_date = df_coletas['date'].max()
    c_date_range = st.sidebar.date_input(
        "Período de Coleta",
        value=(c_min_date, c_max_date),
        min_value=c_min_date,
        max_value=c_max_date
    )
    
    c_carrier_opts = sorted([str(x) for x in df_coletas['carrier'].dropna().unique()])
    c_sel_carrier = st.sidebar.multiselect("Transportadora", options=c_carrier_opts, default=[])
    
    c_uf_opts = sorted([str(x) for x in df_coletas['uf'].dropna().unique()])
    c_sel_uf = st.sidebar.multiselect("UF Destino", options=c_uf_opts, default=[])
    
    # Filtragem
    df_c_filt = df_coletas.copy()
    if isinstance(c_date_range, (tuple, list)) and len(c_date_range) == 2:
        df_c_filt = df_c_filt[
            (df_c_filt['date'] >= c_date_range[0]) & 
            (df_c_filt['date'] <= c_date_range[1])
        ]
    elif isinstance(c_date_range, (tuple, list)) and len(c_date_range) == 1:
        df_c_filt = df_c_filt[df_c_filt['date'] == c_date_range[0]]
        
    if c_sel_carrier:
        df_c_filt = df_c_filt[df_c_filt['carrier'].isin(c_sel_carrier)]
    if c_sel_uf:
        df_c_filt = df_c_filt[df_c_filt['uf'].isin(c_sel_uf)]
        
    if df_c_filt.empty:
        st.warning("Nenhuma coleta encontrada para os filtros selecionados.")
        st.stop()
        
    # KPIs de Coleta
    total_coletas = df_c_filt['quantity'].sum()
    conf_coletas = df_c_filt[df_c_filt['confirmed']]['quantity'].sum()
    pend_coletas = total_coletas - conf_coletas
    
    ckpi1, ckpi2, ckpi3 = st.columns(3)
    with ckpi1:
        render_kpi_card("Total de Coletas", fmt_num(total_coletas), f"{df_c_filt['brand'].nunique()} marcas", "card-ship", 100.0, "#6366f1")
    with ckpi2:
        conf_pct = (conf_coletas / total_coletas * 100) if total_coletas else 0
        render_kpi_card("Confirmado", fmt_num(conf_coletas), f"{fmt_pct(conf_pct)} das coletas", "card-done", conf_pct, "#16a37a")
    with ckpi3:
        pend_pct = (pend_coletas / total_coletas * 100) if total_coletas else 0
        render_kpi_card("A confirmar", fmt_num(pend_coletas), f"{fmt_pct(pend_pct)} das coletas", "card-await", pend_pct, "#ea580c")
        
    st.markdown('<div class="section-title">Coletas por Marca e Loja</div>', unsafe_allow_html=True)
    
    # Tabela por Marca
    brand_col_agg = []
    for brand, bg in df_c_filt.groupby('brand'):
        b_tot = bg['quantity'].sum()
        b_conf = bg[bg['confirmed']]['quantity'].sum()
        b_pend = b_tot - b_conf
        b_conf_pct = (b_conf / b_tot * 100) if b_tot else 0
        b_pend_pct = (b_pend / b_tot * 100) if b_tot else 0
        lojas_count = bg['store'].nunique()
        
        brand_col_agg.append({
            "Marca": brand,
            "Lojas": lojas_count,
            "Total Coletas": b_tot,
            "Confirmado (Qtd)": b_conf,
            "Confirmado (%)": b_conf_pct,
            "A Confirmar (Qtd)": b_pend,
            "A Confirmar (%)": b_pend_pct
        })
        
    df_brand_col = pd.DataFrame(brand_col_agg).sort_values(by="Total Coletas", ascending=False)
    
    if not df_brand_col.empty:
        # Total
        tot_c_row = {
            "Marca": "TOTAL GERAL",
            "Lojas": df_c_filt['store'].nunique(),
            "Total Coletas": total_coletas,
            "Confirmado (Qtd)": conf_coletas,
            "Confirmado (%)": (conf_coletas / total_coletas * 100) if total_coletas else 0,
            "A Confirmar (Qtd)": pend_coletas,
            "A Confirmar (%)": (pend_coletas / total_coletas * 100) if total_coletas else 0
        }
        df_brand_col_display = pd.concat([df_brand_col, pd.DataFrame([tot_c_row])], ignore_index=True)
        
        st.dataframe(
            df_brand_col_display.style.format({
                "Lojas": "{:,.0f}",
                "Total Coletas": "{:,.0f}",
                "Confirmado (Qtd)": "{:,.0f}",
                "Confirmado (%)": "{:.1f}%",
                "A Confirmar (Qtd)": "{:,.0f}",
                "A Confirmar (%)": "{:.1f}%"
            }),
            hide_index=True,
            use_container_width=True
        )
        
        # Detalhamento por Loja
        st.markdown("#### Detalhamento por Loja")
        sel_detail_brand = st.selectbox("Selecione a Marca para ver as lojas:", options=["Todas"] + sorted(df_c_filt['brand'].unique().tolist()))
        
        df_stores = df_c_filt if sel_detail_brand == "Todas" else df_c_filt[df_c_filt['brand'] == sel_detail_brand]
        store_agg = []
        for (br, st_name), sg in df_stores.groupby(['brand', 'store']):
            s_tot = sg['quantity'].sum()
            s_conf = sg[sg['confirmed']]['quantity'].sum()
            s_pend = s_tot - s_conf
            store_agg.append({
                "Marca": br,
                "Loja": st_name,
                "Total": s_tot,
                "Confirmado": s_conf,
                "Confirmado (%)": (s_conf / s_tot * 100) if s_tot else 0,
                "A Confirmar": s_pend,
                "A Confirmar (%)": (s_pend / s_tot * 100) if s_tot else 0
            })
        df_store_summary = pd.DataFrame(store_agg).sort_values(by="Total", ascending=False)
        
        st.dataframe(
            df_store_summary.style.format({
                "Total": "{:,.0f}",
                "Confirmado": "{:,.0f}",
                "Confirmado (%)": "{:.1f}%",
                "A Confirmar": "{:,.0f}",
                "A Confirmar (%)": "{:.1f}%"
            }),
            hide_index=True,
            use_container_width=True
        )
