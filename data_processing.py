"""
Módulo de processamento de dados e regras de negócio para o Painel BF26.
Portado e aprimorado das regras originais em TypeScript / N8N.
"""

import unicodedata
import re
import pandas as pd
import numpy as np
from datetime import datetime

# =====================================================================
# PADRONIZAÇÃO E NORMALIZAÇÃO
# =====================================================================

def normalize(text):
    if text is None or pd.isna(text):
        return ""
    text = str(text)
    # Remove acentos
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', text).strip().lower()

BRAND_MAP = {
    'reserva': 'Reserva',
    'farm': 'Farm',
    'ink': 'INK',
    'oficina': 'Oficina',
    'outlet': 'Outlet',
    'animale': 'Animale',
    'nativozza': 'NV',
    'nv': 'NV',
    'offpremium': 'Off Premium',
    'foxton': 'Foxton',
    'fabula': 'Fábula',
    'crisbarros': 'Cris Barros',
    'mariafilo': 'Maria Filó',
    'carolbassi': 'Carol Bassi',
}

def canonical_brand(raw):
    if raw is None or pd.isna(raw) or str(raw).strip() == "":
        return "Não informada"
    raw_str = str(raw).strip()
    norm = re.sub(r'[^a-z0-9]', '', normalize(raw_str))
    if norm in BRAND_MAP:
        return BRAND_MAP[norm]
    if raw_str.isupper() or raw_str.islower():
        return raw_str.title()
    return raw_str

OPERATION_MAP = {
    '100% cd': '100% CD',
    '100% od': '100% OD',
    'cd soma': 'CD Soma',
    'loja soma': 'Loja Soma',
    'somaplace': 'SomaPlace',
    'misto': 'Misto',
    'loja men': 'Loja Men',
    'loja women': 'Loja Women'
}

def std_operation(v):
    if v is None or pd.isna(v) or str(v).strip() == "":
        return "Não informado"
    t = str(v).strip()
    norm = normalize(t)
    return OPERATION_MAP.get(norm, t)

def translate_gender(v):
    if not v:
        return ""
    v = re.sub(r'\bwom[ae]n\b', 'Feminino', str(v), flags=re.IGNORECASE)
    v = re.sub(r'\bfemale\b', 'Feminino', v, flags=re.IGNORECASE)
    v = re.sub(r'\bm[ae]n\b', 'Masculino', v, flags=re.IGNORECASE)
    v = re.sub(r'\bmale\b', 'Masculino', v, flags=re.IGNORECASE)
    return v

# =====================================================================
# MAPEAMENTO DE STATUS E ETAPAS
# =====================================================================

def map_status(raw):
    s = normalize(raw)
    if any(x in s for x in ['ag. processamento', 'ag processamento', 'aguardando processamento', 'em processamento', 'picking', 'embalado', 'faturado', 'pendente']):
        return 'AG. PROCESSAMENTO', 'processing'
    if any(x in s for x in ['expedido', 'expedidos', 'coletado', 'coletados', 'ag. coleta', 'aguardando coleta']):
        return 'Coletado', 'awaitingCollection'
    if any(x in s for x in ['em transito', 'transito', 'em transporte']):
        return 'Em trânsito', 'transit'
    if any(x in s for x in ['em rota', 'saiu para entrega', 'em rota de entrega']):
        return 'Em rota', 'transit'
    if any(x in s for x in ['entregue', 'entregues', 'entrega realizada']):
        return 'Entregue', 'delivered'
    if any(x in s for x in ['ag. tratativa', 'ag tratativa', 'com ocorrencia', 'ocorrencia', 'extravio', 'devolucao', 'devolvido']):
        return str(raw).strip(), 'incidents'
    return str(raw).strip() if raw else 'Não informado', 'other'

# =====================================================================
# REGRAS DE SLA DE DESPACHO
# =====================================================================

SLA_RULES = {
    'cd rj masculino': (1, 1),
    'cd volo masculino': (1, 1),
    'cd barueri masculino': (3, 3),
    'sfs masculino': (2, 1),
    'sfs feminino': (2, 1),
    'cd rj feminino': (1, 0),
    'cd volo feminino': (3, 2),
}

def is_express(carrier):
    return bool(re.search(r'\bexpress\b', normalize(carrier)))

def get_sla_days(origin, carrier):
    cleaned = re.sub(r'\([^)]*\)', '', str(origin or ''))
    translated = translate_gender(cleaned)
    norm = normalize(translated)
    rule = SLA_RULES.get(norm)
    if rule:
        return rule[1] if is_express(carrier) else rule[0]
    return None

# =====================================================================
# MAPEAMENTO DE COLUNAS DAS PLANILHAS
# =====================================================================

ORDERS_SYNONYMS = {
    'brand': ['MARCA REAL', 'MARCA', 'Marca'],
    'origin': ['ORIGEM REAL', 'ORIGEM', 'Origem'],
    'bu': ['TIPO', 'BU', 'Business Unit', 'Tipo'],
    'sold_at': ['DATA_HORA_INTEGRACAO', 'Data Venda', 'DATA VENDA', 'Data_Venda', 'DATA_INTEGRACAO'],
    'order_id': ['PEDIDO_SITE', 'Pedido', 'Pedido_id', 'ID Pedido', 'Número do Pedido', 'PEDIDO'],
    'uf': ['UF_DESTINO', 'UF', 'UF Destino', 'ESTADO'],
    'carrier': ['TRANSPORTADORA REAL', 'TRANSPORTADORA', 'Transportadora'],
    'delivered_at': ['DT_ENTREGA', 'Data de Entrega', 'DATA_ENTREGA', 'Data Entrega'],
    'operation': ['TIPO_ATENDIMENTO', 'Tipo Atendimento', 'Operação', 'OPERACAO'],
    'status': ['DE X PARA CORRIGIDO', 'Status', 'STATUS', 'SITUACAO'],
    'pieces': ['QTDE_ITENS_UNIFICADA', 'QUANTIDADE DE PEÇAS', 'QTD PEÇAS', 'PEÇAS', 'PECAS'],
    'quantity': ['QUANTIDADE', 'QTD', 'QTDE'],
    'value': ['VALOR DA NOTA - IP', 'Valor da Nota', 'Valor da nota - IP', 'VALOR_NOTA', 'VALOR'],
    'dispatched_at': ['DT DESPACHO_IP', 'DT_DESPACHO_IP', 'Data de despacho', 'DATA DESPACHO', 'DT_DESPACHO'],
}

COLETAS_SYNONYMS = {
    'order_date': ['Data do Pedido', 'DATA DO PEDIDO', 'DATA_PEDIDO', 'Data Pedido', 'DATA'],
    'carrier': ['Transportadora', 'TRANSPORTADORA', 'TRANSPORTADORA REAL'],
    'uf': ['UF Destino', 'UF DESTINO', 'UF_DESTINO', 'UF'],
    'brand': ['Marca', 'MARCA', 'MARCA REAL'],
    'origin': ['Origem', 'ORIGEM', 'ORIGEM REAL'],
    'order_id': ['Número do Pedido', 'Numero do Pedido', 'NUMERO DO PEDIDO', 'Pedido', 'PEDIDO'],
    'store': ['Nome da Loja', 'NOME DA LOJA', 'Loja', 'LOJA', 'Nome Loja'],
    'situation': ['Situação', 'Situacao', 'SITUAÇÃO', 'SITUACAO', 'SITUAÇÃO2', 'Situacao2', 'SITUACAO2'],
    'quantity': ['Quantidade', 'QUANTIDADE', 'QTD', 'QTDE']
}

def find_column(df, synonyms):
    col_map = {normalize(c): c for c in df.columns}
    for syn in synonyms:
        n = normalize(syn)
        if n in col_map:
            return col_map[n]
    return None

def parse_currency(val):
    if pd.isna(val) or val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val) if np.isfinite(val) else 0.0
    s = str(val).replace('R$', '').replace(' ', '').strip()
    if not s:
        return 0.0
    if ',' in s:
        s = s.replace('.', '').replace(',', '.')
    try:
        n = float(s)
        return n if np.isfinite(n) else 0.0
    except ValueError:
        return 0.0

# =====================================================================
# CARREGAMENTO E PROCESSAMENTO DE PEDIDOS
# =====================================================================

def process_orders_dataframe(df_raw):
    """
    Normaliza e enriquece o DataFrame de pedidos com todas as métricas
    necessárias para o painel.
    """
    mapped = {}
    for canonical, syns in ORDERS_SYNONYMS.items():
        col = find_column(df_raw, syns)
        if col is not None:
            mapped[canonical] = df_raw[col]
        else:
            mapped[canonical] = None

    # Verificação de colunas obrigatórias
    reqs = ['brand', 'carrier', 'origin', 'bu', 'sold_at', 'uf', 'status']
    missing = [r for r in reqs if mapped[r] is None]
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes na planilha: {', '.join(missing)}")

    df = pd.DataFrame()
    df['order_id'] = mapped['order_id'] if mapped['order_id'] is not None else [f"PED-{i}" for i in range(len(df_raw))]
    df['brand'] = mapped['brand'].apply(canonical_brand)
    df['origin'] = mapped['origin'].astype(str).str.strip().replace({'nan': 'Não informada', '': 'Não informada'})
    df['bu'] = mapped['bu'].astype(str).str.strip().replace({'nan': 'Não informado', '': 'Não informado'})
    df['carrier'] = mapped['carrier'].astype(str).str.strip().replace({'nan': 'Não informada', '': 'Não informada'})
    df['uf'] = mapped['uf'].astype(str).str.strip().str.upper().replace({'nan': 'Não informada', '': 'Não informada'})
    df['operation'] = mapped['operation'].apply(std_operation) if mapped['operation'] is not None else 'Não informado'

    # Tratamento de datas
    df['sold_at'] = pd.to_datetime(mapped['sold_at'], errors='coerce', dayfirst=True)
    df = df.dropna(subset=['sold_at']).copy() # Descarte de linhas sem data de venda
    df['sold_date'] = df['sold_at'].dt.date

    # Data de entrega
    if mapped['delivered_at'] is not None:
        df['delivered_at'] = pd.to_datetime(mapped['delivered_at'], errors='coerce', dayfirst=True)
    else:
        df['delivered_at'] = pd.NaT

    # Data de despacho
    if mapped['dispatched_at'] is not None:
        df['dispatched_at'] = pd.to_datetime(mapped['dispatched_at'], errors='coerce', dayfirst=True)
    else:
        df['dispatched_at'] = pd.NaT

    # Status e Stage
    status_and_stage = mapped['status'].apply(map_status)
    df['status'] = [s[0] for s in status_and_stage]
    df['stage'] = [s[1] for s in status_and_stage]

    # Quantidade de pedidos (1 por linha)
    df['quantity'] = 1

    # Peças
    if mapped['pieces'] is not None:
        df['pieces'] = mapped['pieces'].apply(parse_currency)
    elif mapped['quantity'] is not None:
        df['pieces'] = mapped['quantity'].apply(parse_currency)
    else:
        df['pieces'] = 1.0

    # Valor da nota
    if mapped['value'] is not None:
        df['value'] = mapped['value'].apply(parse_currency)
    else:
        df['value'] = 0.0

    # Lead time de entrega em horas e dias (apenas quando entregue e coerente)
    lead_delivery_hours = (df['delivered_at'] - df['sold_at']).dt.total_seconds() / 3600.0
    valid_delivery = (df['delivered_at'].notna()) & (lead_delivery_hours >= 0)
    df['delivery_lead_hours'] = np.where(valid_delivery, lead_delivery_hours, np.nan)
    df['delivery_lead_days'] = df['delivery_lead_hours'] / 24.0

    # Lead time de despacho em dias corridos
    # (data despacho - data venda em dias corridos base calendário)
    disp_date = df['dispatched_at'].dt.date
    sold_date = df['sold_at'].dt.date
    valid_dispatch = (df['dispatched_at'].notna()) & (df['dispatched_at'] >= df['sold_at'])
    df['dispatch_lead_hours'] = np.where(valid_dispatch, (df['dispatched_at'] - df['sold_at']).dt.total_seconds() / 3600.0, np.nan)
    df['dispatch_lead_days'] = np.where(
        valid_dispatch,
        (pd.to_datetime(disp_date) - pd.to_datetime(sold_date)).dt.days,
        np.nan
    )

    # SLA Rules
    df['sla_days'] = [get_sla_days(o, c) for o, c in zip(df['origin'], df['carrier'])]
    df['has_sla_rule'] = df['sla_days'].notna()
    
    # SLA atingido (para pedidos despachados)
    df['sla_met'] = np.where(
        df['has_sla_rule'] & df['dispatch_lead_days'].notna(),
        df['dispatch_lead_days'] <= df['sla_days'],
        np.nan
    )

    # Backlog acima do SLA: pedidos ainda em processamento cuja idade ultrapassa o SLA
    max_sold_date = df['sold_date'].max()
    age_days = (pd.to_datetime(max_sold_date) - pd.to_datetime(df['sold_date'])).dt.days
    df['is_overdue'] = (
        (df['stage'] == 'processing') &
        df['has_sla_rule'] &
        (age_days > df['sla_days'])
    )

    return df

# =====================================================================
# CARREGAMENTO E PROCESSAMENTO DE COLETAS
# =====================================================================

def map_coleta_situation(raw):
    s = normalize(raw)
    if any(x in s for x in ['confirmado', 'cobrar movimentacao', 'ag. movimentacao', 'ag movimentacao', 'aguardando movimentacao']):
        return 'Confirmado', True
    if any(x in s for x in ['a confirmar', 'aguardando', 'ag. coleta', 'ag coleta', 'aguardando coleta', 'problema integracao', 'problema de integracao']):
        return 'A confirmar', False
    return str(raw).strip() if raw else 'Não informado', False

def process_coletas_dataframe(df_raw):
    mapped = {}
    for canonical, syns in COLETAS_SYNONYMS.items():
        col = find_column(df_raw, syns)
        mapped[canonical] = df_raw[col] if col is not None else None

    reqs = ['order_date', 'carrier', 'uf', 'brand', 'origin', 'order_id', 'store', 'situation']
    missing = [r for r in reqs if mapped[r] is None]
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes na planilha de coletas: {', '.join(missing)}")

    df = pd.DataFrame()
    df['order_id'] = mapped['order_id'].astype(str).str.strip()
    df['brand'] = mapped['brand'].apply(canonical_brand)
    df['carrier'] = mapped['carrier'].astype(str).str.strip()
    df['origin'] = mapped['origin'].astype(str).str.strip()
    df['uf'] = mapped['uf'].astype(str).str.strip().str.upper()
    df['store'] = mapped['store'].astype(str).str.strip()
    
    df['order_date'] = pd.to_datetime(mapped['order_date'], errors='coerce', dayfirst=True)
    df = df.dropna(subset=['order_date']).copy()
    df['date'] = df['order_date'].dt.date

    sit_res = mapped['situation'].apply(map_coleta_situation)
    df['situation_desc'] = [s[0] for s in sit_res]
    df['confirmed'] = [s[1] for s in sit_res]

    if mapped['quantity'] is not None:
        df['quantity'] = mapped['quantity'].apply(parse_currency)
        df['quantity'] = df['quantity'].replace(0, 1)
    else:
        df['quantity'] = 1

    return df
