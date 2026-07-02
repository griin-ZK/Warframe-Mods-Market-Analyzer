import re
import requests

# Timeout (seconds) applied to every outbound call to warframe.market.
# Without this, a slow/hanging upstream response can hang a worker
# indefinitely and exhaust the whole Flask process (DoS).
REQUEST_TIMEOUT = 5

# Slugs from warframe.market are lowercase alphanumeric with underscores/hyphens.
# Anything else is rejected before it's ever placed into a URL.
_SLUG_RE = re.compile(r"^[a-z0-9_\-]+$")


def is_valid_slug(slug: str) -> bool:
    """
    Validate that a slug looks like a real warframe.market slug before
    using it to build an outbound request. Prevents this app from being
    used as an open relay/proxy for arbitrary requests to warframe.market.
    """
    return isinstance(slug, str) and 1 <= len(slug) <= 100 and bool(_SLUG_RE.match(slug))


def get_items_wf_market():
    """
    Connect to wf_market api of items (v2)
    """
    
    url = "https://api.warframe.market/v2/items"
    
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
    except requests.RequestException:
        return -1
    
    if response.status_code != 200:
        return -1
    
    return response.json().get("data",{})



def get_top_order_item(slug : str ,isTop : bool):
    """
    Get orders of a certain item if isTop is True then get best 5 offers
    """
    if not is_valid_slug(slug):
        return -1

    if isTop:
        url = f"https://api.warframe.market/v2/orders/item/{slug}/top"
    else:
        url = f"https://api.warframe.market/v2/orders/item/{slug}"
    
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
    except requests.RequestException:
        return -1

    if response.status_code != 200:
        return -1
    
    return response.json().get("data",{})


def only_sell_or_buy_statistics_filter(orders,isSell = True):
    """
    divide for sell and buy
    """
    
    stats_48h = orders.get("48hours",{})
    stats_90d = orders.get("90days",{})
    
    if isSell:
        
        stats_48h_flt = [blocco for blocco in stats_48h if blocco.get("order_type","sell") == "sell"]
        stats_90d_flt = [blocco for blocco in stats_90d if blocco.get("order_type","sell") == "sell"]
    
    else:
        
        stats_48h_flt = [blocco for blocco in stats_48h if blocco.get("order_type","sell") == "buy"]
        stats_90d_flt = [blocco for blocco in stats_90d if blocco.get("order_type","sell") == "buy"]
        
    
        
    return {"48h" : stats_48h_flt, "90d" : stats_90d_flt}

def filter_mods(list_dicta,mod_rank_range = [0,3],records_for_avg = -1 ) -> dict:
    """
    Evaluate mods value given avg_price and volume sum
    """

    # mod_rank_range values (e.g. maxRank from the items API) can be None
    # or otherwise non-numeric for malformed/unexpected catalog entries.
    # Coerce defensively instead of letting int(None) raise TypeError and
    # take down the whole batch endpoint over one bad item.
    try:
        rank_0 = int(mod_rank_range[0])
    except (TypeError, ValueError):
        rank_0 = 0
    try:
        rank_max = int(mod_rank_range[1])
    except (TypeError, ValueError):
        rank_max = rank_0

    def _safe_int(value, default=0):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    # Also guard each record: skip entries missing required fields or with
    # non-numeric values rather than throwing KeyError/ValueError.
    clean = []
    for block in list_dicta:
        if not all(k in block for k in ("volume", "wa_price", "mod_rank")):
            continue
        clean.append({
            "volume": _safe_int(block["volume"]),
            "wa_price": _safe_int(block["wa_price"]),
            "mod_rank": _safe_int(block["mod_rank"], default=0),
        })

    volume_sum_rank_0 =   sum(b['volume'] for b in clean if b['mod_rank'] == rank_0)
    volume_sum_rank_max = sum(b['volume'] for b in clean if b['mod_rank'] == rank_max)
    avg_wa_price_rank_0 = 0
    avg_wa_price_rank_max = 0
    
    if volume_sum_rank_0 > 0:
        avg_wa_price_rank_0 = sum(b['volume'] * b['wa_price'] for b in clean if b['mod_rank'] == rank_0) / volume_sum_rank_0
    if volume_sum_rank_max > 0:
        avg_wa_price_rank_max = sum(b['volume'] * b['wa_price'] for b in clean if b['mod_rank'] == rank_max) / volume_sum_rank_max
    
    return {"rank_0" : {'volume' : volume_sum_rank_0,'price' : avg_wa_price_rank_0}, "rank_max" : {'volume' : volume_sum_rank_max,'price' : avg_wa_price_rank_max}}

    

def get_statistics_orders_item(slug : str,isLive = True,sellOrder = True):
    
    """
    Get statistics of completed orders
    """
    
    
    if not is_valid_slug(slug):
        return -1

    url = f"https://api.warframe.market/v1/items/{slug}/statistics"
    
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
    except requests.RequestException:
        return -1
    
    if response.status_code != 200:
        return -1
    
    if not isLive:
        data = "statistics_closed"
    else:
        data = "statistics_live"
    
    #return response.json().get("payload",{})
    return only_sell_or_buy_statistics_filter(response.json().get("payload",{}).get(data,{}),sellOrder)

    

def get_flags_from_dict(list_dicta,flags):
    """
    Return dict only with certain flags
    """
    return [{coppia:item[coppia] for coppia in flags if coppia in item} for item in list_dicta]

  
def get_galvanized_mods(items):
    adder = {}
    counter = 0
    for element in items:
        slug_lower = element['slug'].lower()
        if "galvanized" in slug_lower:
            slug = element['slug']
            tags = element['tags']
            id = element['id']
            # Some catalog entries lack maxRank entirely; default to 0
            # rather than letting int(None) crash the whole /galvs page.
            max_rank = element.get("maxRank") or 0
            adder[counter] = {
                            "id" : id,
                            "slug" : slug,
                            "maxRank" : max_rank,
                            "tags" : tags,
                            "ref" : element['gameRef']
                            }
            counter += 1
    return adder
def get_syndicates_items(items,factions : list[str]):
    """
    Get all augmented mods from eelected syndicates
    
    
    """
    print(f" --- DEBUG my factions {factions} --- ")
    SYNDICATE_WARFRAMES = {
    "steelmeridian": [
        "atlas","citrine", "ember", "excalibur", "frost", "garuda", 
        "grendel","khora","kullervo", "mesa", "nezha","nidus","nova","oberon",
        "qorvex", "rhino", "saryn","temple", "vauban", "xaku"
    ],
    "arbitersofhexis": [
        "ash", "baruuk", "dante", "equinox", "excalibur", "excaliburumbra", "gara","gauss",
        "gyre", "harrow", "inaros","jade","koumei","limbo","loki", "mirage", "nyx","protea",
        "styanax","volt","wukong"
    ],
    "cephalonsuda": [
        "banshee", "caliban","chroma","dante", "frost", "hildryn","hydroid","ivara", "limbo",  
        "mirage", "nezha", "nova", "octavia", "qorvex","revenant","sevagoth","vauban", "wisp","xaku","yareli"
    ],
    "perrinsequence": [
        "banshee", "caliban", "chroma","dagath", "gauss", "gyre", "hildryn", "inaros", 
        "ivara", "mag", "nekros", "nidus", "nokko", "protea", 
        "revenant", "rhino", "sevagoth", "trinity", "valkyr", "vauban"
    ],
    "redveil": [
        "ash","atlas","citrine","dagath","ember","excaliburumbra","garuda", "grendel" , "harrow", "jade" , "khora" , 
        "lavos" , "loki", "mesa",  "nekros",  "nokko",  "saryn" ,  "titania" ,  "volt",  "voruna", "zephyr"
    ],
    "newloka": [
       "baruuk",  "equinox" ,  "gara" ,  "hydroid" ,  "koumei" ,  "kullervo" ,  "lavos" ,  "mag" ,  "nyx" ,
        "oberon",  "octavia", "styanax" ,  "temple" ,  "titania",  "trinity",  "valkyr",  "wisp",  "wukong",
        "yareli", "zephyr"
    ]
    }
    
    adder = {}
    counter = 0
    syndicates_mod = []
    for element in items:
        ref_lower = element['gameRef'].lower()
        
        try:
            wF = ref_lower.split('/')[3]
            """
            This check filters mods from other non important items
            """
        except:
            continue
        syndicates_mod = []
        tags = element['tags']
        for synd in factions:
            
            if any( wf in tags for wf in SYNDICATE_WARFRAMES[synd] ) and "augment" in ref_lower:
                #print( " --------------------------------------------- ")
                #print(f" --- DEBUG {wF} in faction {synd} --- ")
                #print(f" --- DEBUG mod_name {element['slug']} --- ")
                #print( " --------------------------------------------- ")
                syndicates_mod.append(synd)
        
        if len(syndicates_mod) >= 1:
            slug = element['slug']
            
            id = element['id']
            # Default maxRank to 0 rather than None to avoid int(None)
            # crashing the whole batch downstream in filter_mods.
            max_rank = element.get("maxRank") or 0
            adder[counter] = {
                            "id" : id,
                            "slug" : slug,
                            "maxRank" : max_rank,
                            "tags" : tags,
                            "ref" : element['gameRef'],
                            "syndicate" : syndicates_mod
                            }
            counter += 1
    
    return adder