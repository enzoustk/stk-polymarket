import time
import json
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from stk_polymarket.api.config import URLS
from stk_polymarket.api.modules import helpers
from loading_animation.animation import loading_animation

def update(
    save_file: bool = True,
    file_path: str = '../files/all_markets.json',
    save_debug: bool = False
    ):
    
    offset = 0
    limit = 50
    
    mapa_tokens = {}
    
    total_events = 0
    total_tokens = 0
    total_markets = 0

    # --- CONFIGURAÇÃO DE SESSÃO ROBUSTA ---
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504, 429],
        allowed_methods=["GET"]
    )
    session.mount('https://', HTTPAdapter(max_retries=retries))
    # --------------------------------------
    with loading_animation(
        "Starting to update Markets from Polymarket..."
    ) as status:
        while True:
            params = {
                "closed": "false",
                "limit": str(limit),
                "offset": str(offset),
                "order": "id",
                "ascending": "false",
                "related_tags": "true"
            }

            status['message'] = (f"Fetching batch: offset={offset}, limit={limit}")

            try:
                response = session.get(URLS['GAMMA_EVENTS_URL'], params=params, timeout=10)
                response.raise_for_status()
                events = response.json()

                status['message'] = (f"Retrieved {len(events)} events")

                if not events:
                    status['message'] = ("No more events. Finishing.")
                    break
                
                for event in events:
                    total_events += 1

                    # Tags
                    tags_obj = event.get("tags", [])
                    event_tags = [
                        t["slug"] for t in tags_obj
                        if isinstance(t, dict) and "slug" in t
                    ]
                    
                    # --- NOVO: Detectar Esporte ---
                    detected_sport = helpers.get_sport_from_tags(event_tags)

                    markets = event.get("markets", [])
                    total_markets += len(markets)

                    for market in markets:
                        question = market.get("question") or event.get("title")
                        condition_id = market.get("conditionId") or market.get("condition_id")

                        if not condition_id:
                            continue

                        raw_clob_ids = market.get("clobTokenIds")
                        raw_outcomes = market.get("outcomes")
                        start_time = event.get("startTime")

                        # Parse safely
                        if isinstance(raw_clob_ids, str):
                            try:
                                clob_ids = json.loads(raw_clob_ids)
                            except:
                                clob_ids = []
                        else:
                            clob_ids = raw_clob_ids

                        if isinstance(raw_outcomes, str):
                            try:
                                outcomes = json.loads(raw_outcomes)
                            except:
                                outcomes = []
                        else:
                            outcomes = raw_outcomes

                        if isinstance(clob_ids, list) and isinstance(outcomes, list):
                            if len(clob_ids) == len(outcomes):
                                for i, t_id in enumerate(clob_ids):
                                    mapa_tokens[t_id] = {
                                        "question": question,
                                        "outcome": outcomes[i],
                                        "condition_id": condition_id,
                                        "tags": event_tags,
                                        "sport": detected_sport,
                                        "start_time": start_time
                                    }
                                    total_tokens += 1
                        
                        if save_debug:            
                            if total_events == 1:
                                with open('event_debug.json', 'w', encoding='utf-8') as f:
                                    json.dump(event, f, indent=4, ensure_ascii=False)
                                print("📝 Saved event_debug.json for inspection.")
                    
                status['message'] = (f"Progress: events={total_events}, markets={total_markets}, tokens={total_tokens}")

                offset += limit
                # Pequena pausa para evitar sobrecarregar a CPU ou API
                time.sleep(0.2)

            except requests.exceptions.RequestException as e:
                print(f"Network error on offset {offset}: {e}")
                print("Retrying batch in 5 seconds...")
                time.sleep(5)
                # Nota: Como estamos num while True e não incrementamos o offset aqui,
                # ele vai tentar o mesmo batch novamente na próxima volta.
                continue

            except Exception as e:
                print(f"Critical Error: {e}")
                break

    # Save
    if save_file:
        print("Saving output...")
        with open(file_path, "w", encoding='utf-8') as f:
            json.dump(mapa_tokens, f, indent=2, ensure_ascii=False)

        print(f"Saved {total_tokens} tokens to {file_path}")
    print(f"Market Fetching Ended. Found {total_tokens} tokens.")
    
    return mapa_tokens