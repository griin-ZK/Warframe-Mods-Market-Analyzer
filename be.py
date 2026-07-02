import requests

def get_items_wf_market():
    """
    Connect to wf_market api of items (v2)
    """
    
    url = "https://api.warframe.market/v2/items"
    
    response = requests.get(url)
    
    
    if response.status_code != 200:
        return -1
    
    return response.json().get("data",{})



def get_top_order_item(slug : str ,isTop : bool):
    """
    Get orders of a certain item if isTop is True then get best 5 offers
    """
    if isTop:
        url = f"https://api.warframe.market/v2/orders/item/{slug}/top"
    else:
        url = f"https://api.warframe.market/v2/orders/item/{slug}"
    
    response = requests.get(url)
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
    
    
    volume_sum_rank_0 =   sum(int(block['volume']) for block in list_dicta if int(block['mod_rank']) == mod_rank_range[0])
    volume_sum_rank_max = sum(int(block['volume']) for block in list_dicta if int(block['mod_rank']) == mod_rank_range[1])
    avg_wa_price_rank_0 = 0
    avg_wa_price_rank_max = 0
    
    if volume_sum_rank_0 > 0:
        
        avg_wa_price_rank_0 = sum(int(block['volume']) * int(block["wa_price"]) for block in list_dicta if int(block['mod_rank']) == mod_rank_range[0]) / volume_sum_rank_0
    if volume_sum_rank_max > 0:
        avg_wa_price_rank_max = sum(int(block['volume']) * int(block["wa_price"]) for block in list_dicta if int(block['mod_rank']) == mod_rank_range[1]) / volume_sum_rank_max
    
    return {"rank_0" : {'volume' : volume_sum_rank_0,'price' : avg_wa_price_rank_0}, "rank_max" : {'volume' : volume_sum_rank_max,'price' : avg_wa_price_rank_max}}

    

def get_statistics_orders_item(slug : str,isLive = True,sellOrder = True):
    
    """
    Get statistics of completed orders
    """
    
    
    url = f"https://api.warframe.market/v1/items/{slug}/statistics"
    
    response = requests.get(url)
    
    
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
            max_rank = element.get("maxRank")
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
    SYNDICATE_WARFRAMES = {
    "steelmeridian": [
        "atlas","citrine", "ember", "excalibur", "frost", "garuda", 
        "grendel","khora","kullervo", "mesa", "nezha","nidus","nova","oberon",
        "qorvex", "rhino", "saryn","temple", "vauban", "xaku"
    ],
    "arbitersofhexis": [
        "ash", "baruuk", "dante", "equinox", "excalibur", "excaliburumbra", "gara","gauss" 
        "gyre", "harrow", "inaros","jade","koumei","limbo","loki", "mirage", "nyx","protea",
        "styanax","volt","wukong"
    ],
    "cephalonsuda": [
        "banshee", "caliban","chroma","dante", "frost", "hildryn","hydroid","ivara", "limbo",  
        "mirage", "nezha", "nova", "octavia", "qorvex","revenant","sevagoth","vauban", "wisp","xaku","yareli"
    ],
    "perrinsequence": [
        "banshee", "caliban", "chroma","dagath", "gauss", "gyre", "hyldrin", "inaros", 
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
        except:
            continue
        syndicates_mod = []
        for synd in factions:
            
            if wF in SYNDICATE_WARFRAMES[synd] and "augment" in ref_lower:
                syndicates_mod.append(synd)
        
        if len(syndicates_mod) >= 1:
            slug = element['slug']
            tags = element['tags']
            id = element['id']
            max_rank = element.get("maxRank")
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
