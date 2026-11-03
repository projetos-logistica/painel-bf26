"""
Armazenamento local persistente em arquivos Parquet + Metadata JSON.
Substitui completamente a dependência do SQL Server, garantindo acesso
compartilhado para os times SOMA e Reserva sem necessidade de banco de dados externo.
"""

import os
import json
import pandas as pd
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
METADATA_FILE = os.path.join(DATA_DIR, "metadata.json")

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)

def load_metadata():
    ensure_data_dir()
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_metadata(meta):
    ensure_data_dir()
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

def save_orders_dataset(df, filename="planilha_pedidos.xlsx", author="Usuário"):
    ensure_data_dir()
    path = os.path.join(DATA_DIR, "pedidos.parquet")
    df.to_parquet(path, index=False)
    
    meta = load_metadata()
    meta["orders"] = {
        "filename": filename,
        "rows": len(df),
        "updated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "author": author,
        "path": path
    }
    save_metadata(meta)

def load_orders_dataset():
    path = os.path.join(DATA_DIR, "pedidos.parquet")
    if os.path.exists(path):
        try:
            return pd.read_parquet(path)
        except Exception:
            return None
    return None

def save_coletas_dataset(df, filename="planilha_coletas.xlsx", author="Usuário"):
    ensure_data_dir()
    path = os.path.join(DATA_DIR, "coletas.parquet")
    df.to_parquet(path, index=False)
    
    meta = load_metadata()
    meta["coletas"] = {
        "filename": filename,
        "rows": len(df),
        "updated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "author": author,
        "path": path
    }
    save_metadata(meta)

def load_coletas_dataset():
    path = os.path.join(DATA_DIR, "coletas.parquet")
    if os.path.exists(path):
        try:
            return pd.read_parquet(path)
        except Exception:
            return None
    return None
