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
 
# Adicionar no final do arquivo stk_polymarket/api/modules/helpers.py

def get_sport_from_tags(tags: list) -> str:
    """
    Recebe uma lista de slugs (ex: ['sports', 'basketball', 'nba'])
    e retorna o esporte principal normalizado.
    """
    # Mapeamento de tags para esportes principais
    # A ordem importa: termos mais específicos primeiro se houver conflito
    sport_map = {
        'ncaa-basketball': 'basketball',
        'ncaa-football': 'football',
        'soccer': 'soccer',
        'football': 'soccer', # Polymarket as vezes usa football para soccer
        'uefa': 'soccer',
        'premier-league': 'soccer',
        'la-liga': 'soccer',
        'basketball': 'basketball',
        'nba': 'basketball',
        'euroleague': 'basketball',
        'tennis': 'tennis',
        'atp': 'tennis',
        'wta': 'tennis',
        'american-football': 'football', # NFL
        'nfl': 'football',
        'mma': 'mma',
        'ufc': 'mma',
        'boxing': 'boxing',
        'formula-1': 'racing',
        'baseball': 'baseball',
        'mlb': 'baseball',
        'ice-hockey': 'hockey',
        'nhl': 'hockey'
    }

    # Verifica cada tag do evento
    for tag in tags:
        tag_lower = str(tag).lower()
        if tag_lower in sport_map:
            return sport_map[tag_lower]
            
    return "other"