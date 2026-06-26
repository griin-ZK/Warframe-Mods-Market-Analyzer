from flask import Flask, render_template, jsonify, request
import requests
import be
app = Flask(__name__)

# Basic HTML template string for lightning-fast setup without extra files


@app.route('/')
def home():
    return render_template("./index.html",active_page='syndicates')

@app.route('/raw_stats_item/<slug>')
def raw_stats(slug):
    orders = be.get_statistics_orders_item(slug,True,True)
    return jsonify(orders)

@app.route('/syndicates', methods=['POST'])
def syndicates_post():
    
    items = be.get_items_wf_market()
    if items == -1:
        return jsonify({"error": "Impossibile connettersi a Warframe Market, possibile RateLimit"}), 500
    
    factions = request.form.getlist('factions')
    all_facts = [
        "steelmeridian","arbitersofhexis","cephalonsuda","perrinsequence","redveil","newloka"
    ]
    
    if not factions:
        factions = all_facts
    
    
    #print(f"Fazioni selezionate: {factions}")
    
    adder = be.get_syndicates_items(items,factions)
    #print(adder)
    final = {}
    
    for item in adder.values():
        #print("ITEM" , item)
        #orders = be.get_top_order_item(item["slug"],False)
        orders = be.get_statistics_orders_item(item["slug"],True,True)
        
        if orders == -1:
            return jsonify({"error": "Impossibile connettersi a Warframe Market, possibile RateLimit "}), 500
        
        stats_per_hours_48h = be.get_flags_from_dict(orders.get("48h"), ['datetime','wa_price','mod_rank','volume'])
        stats_per_hours_90d = be.get_flags_from_dict(orders.get("90d"), ['datetime','wa_price','mod_rank','volume'])
        
        #print(item['slug'],item['maxRank'])
        mods_syndicates_filter = be.filter_mods(stats_per_hours_48h,[0,int(item['maxRank'])])
        mods_syndicates_filter['syndicate'] = item['syndicate']
        final[item["slug"]] = mods_syndicates_filter
        
    final = dict(sorted(
        final.items(), 
        key=lambda item: item[1]['rank_max']['price'], 
        reverse=True
        ))
        
    return render_template('results.html', data=final,active_page='syndicates')


@app.route('/galvs', methods=['GET'])
def galvanized_post():
    items = be.get_items_wf_market()
    if items == -1:
            return jsonify({"error": "Impossibile connettersi a Warframe Market, possibile RateLimit"}), 500

    adder = be.get_galvanized_mods(items)
    final = {}
    for item in adder.values():
        orders = be.get_statistics_orders_item(item["slug"],True,True)
        if orders == -1:
            return jsonify({"error": "Impossibile connettersi a Warframe Market, possibile RateLimit "}), 500
        
        stats_per_hours_48h = be.get_flags_from_dict(orders.get("48h"), ['datetime','wa_price','mod_rank','volume'])
        stats_per_hours_90d = be.get_flags_from_dict(orders.get("90d"), ['datetime','wa_price','mod_rank','volume'])
        
        #print(item['slug'],item['maxRank'])
        
        mods_filter = be.filter_mods(stats_per_hours_48h,[0,int(item['maxRank'])])
        final[item["slug"]] = mods_filter
        
    final = dict(sorted(
        final.items(), 
        key=lambda item: item[1]['rank_max']['price'], 
        reverse=True
        ))
    #return jsonify(final)
    return render_template('galvs.html', data=final,active_page='galvs')


    
@app.route('/items')
def items():
    
    
    url = "https://api.warframe.market/v2/items"
    response = requests.get(url)
    if response.status_code != 200:
        return jsonify({"error": "Impossibile connettersi a Warframe Market"}), 500
    
    items = response.json().get("data",{})
    

    
    return jsonify(items)

if __name__ == '__main__':
    # debug=True automatically reloads the server when you make changes
    app.run()