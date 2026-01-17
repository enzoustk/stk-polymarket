import pandas as pd

def safe_divide(num, den, fallback=None):
    try: return num/den
    except: return fallback

def assertion_active(
    active_df: pd.DataFrame,
    closed_df: pd.DataFrame,
    ) -> pd.DataFrame:

    # Cria cópias para não modificar os originais
    active_df = active_df.copy()
    closed_df = closed_df.copy()

    # Identifica posições realmente ativas (redeemable == False)
    real_active_mask = active_df['redeemable'] == False
    
    # Adiciona coluna 'ativo' para active_df
    active_df['active'] = real_active_mask
    
    # Adiciona coluna 'ativo' para closed_df (todas False)
    closed_df['active'] = False
    
    # Combina os dois DataFrames
    return pd.concat([active_df, closed_df], ignore_index=True)
 
