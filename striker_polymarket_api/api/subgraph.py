"""
Contém as funções da API subgraph para puxar posições de forma mais eficiente
fetch_pnl_data -> todas as posições e PnLs
fetch_closed_pnl_data -> só fechadas
fetch_live_pnl_data -> só abertas
"""


import pandas as pd
from striker_polymarket_api.api.modules.subgraph_api.fetch_subgraph import (
    split_positions,
    get_all_user_positions,
    fetch_positions_from_rest
)


def fetch_pnl_data(
    user_address: str,
    ) -> pd.DataFrame:
    """
    Função principal orquestradora (com várias animações).
    """
    
    print(
        f"Iniciando coleta de dados para: {user_address} (Todas as posições)"
    )
    
    # Buscar Todas as Posições
    active_positions, closed_positions = split_positions(
        get_all_user_positions(user_address)
    )
    
    active_df = fetch_positions_from_rest(
        user_address,
        active_positions,
        closed=False
    )
    
    closed_df = fetch_positions_from_rest(
        user_address,
        closed_positions,
        closed=True
    )
    
    return closed_df, active_df


def fetch_closed_pnl_data(
    user_address: str,
    ) -> pd.DataFrame:
    """
    Função principal orquestradora (com várias animações).
    """
    print(f"Iniciando coleta de dados para: {user_address}")
    
    
    # Buscar Todas as Posições
    _, closed_positions = split_positions(
        get_all_user_positions(user_address)
    )
    
    # Aqui começa a lógica de puxar dados em rest
    # Retorna em pd.DataFrame
    closed_positions = fetch_positions_from_rest(
        user_address,
        closed_positions,
        closed=True
    )
    
    return closed_positions


def fetch_live_pnl_data(
    user_address: str,
    ) -> pd.DataFrame:
    """
    Função principal orquestradora (com várias animações).
    """
    print(f"Iniciando coleta de dados para: {user_address}")
    
    
    # Buscar Todas as Posições
    active_positions, _ = split_positions(
        get_all_user_positions(user_address)
    )
    
    # Aqui começa a lógica de puxar dados em rest
    # Retorna em pd.DataFrame
    active_df = fetch_positions_from_rest(
        user_address,
        active_positions,
        closed=False
    )
    
    return active_df