from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

OFF_BASE = "https://world.openfoodfacts.org"
HEADERS = {"User-Agent": "InventoryManagementFlask/1.0 (student project)"}

# In-memory "database"
inventory = [
    {"id": 1, "product_name": "Almond Milk", "brands": "Silk", "barcode": "0025293001077",
     "ingredients_text": "Filtered water, almonds", "price": 3.99, "stock": 25},
    {"id": 2, "product_name": "Peanut Butter", "brands": "Jif", "barcode": "0051500255162",
     "ingredients_text": "Roasted peanuts, sugar", "price": 4.50, "stock": 40},
]
next_id = 3


def get_next_id():
    global next_id
    current = next_id
    next_id += 1
    return current


def find_item(item_id):
    return next((i for i in inventory if i["id"] == item_id), None)


# ---------- External API helpers (OpenFoodFacts) ----------
def normalize_product(product, barcode=None):
    return {
        "product_name": product.get("product_name") or "Unknown",
        "brands": product.get("brands", ""),
        "barcode": product.get("code") or barcode or "",
        "ingredients_text": product.get("ingredients_text", ""),
    }


def fetch_product_by_barcode(barcode):
    url = f"{OFF_BASE}/api/v2/product/{barcode}.json"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != 1:
        return None
    return normalize_product(data["product"], barcode)


def search_products_by_name(name):
    params = {"search_terms": name, "search_simple": 1, "action": "process",
              "json": 1, "page_size": 5}
    resp = requests.get(f"{OFF_BASE}/cgi/search.pl", params=params,
                        headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return [normalize_product(p) for p in resp.json().get("products", [])]


# ---------- CRUD routes ----------
@app.route("/inventory", methods=["GET"])
def get_inventory():
    return jsonify(inventory), 200


@app.route("/inventory/<int:item_id>", methods=["GET"])
def get_item(item_id):
    item = find_item(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404
    return jsonify(item), 200


@app.route("/inventory", methods=["POST"])
def create_item():
    data = request.get_json(silent=True) or {}
    if not data.get("product_name"):
        return jsonify({"error": "product_name is required"}), 400
    item = {
        "id": get_next_id(),
        "product_name": data["product_name"],
        "brands": data.get("brands", ""),
        "barcode": data.get("barcode", ""),
        "ingredients_text": data.get("ingredients_text", ""),
        "price": data.get("price", 0.0),
        "stock": data.get("stock", 0),
    }
    inventory.append(item)
    return jsonify(item), 201


@app.route("/inventory/<int:item_id>", methods=["PATCH"])
def update_item(item_id):
    item = find_item(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404
    data = request.get_json(silent=True) or {}
    for key in ("product_name", "brands", "barcode", "ingredients_text", "price", "stock"):
        if key in data:
            item[key] = data[key]
    return jsonify(item), 200


@app.route("/inventory/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    item = find_item(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404
    inventory.remove(item)
    return jsonify({"message": "Item deleted"}), 200


# ---------- External API routes ----------
@app.route("/external/barcode/<barcode>", methods=["GET"])
def external_barcode(barcode):
    try:
        product = fetch_product_by_barcode(barcode)
    except requests.RequestException as e:
        return jsonify({"error": f"External API error: {e}"}), 502
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product), 200


@app.route("/external/search", methods=["GET"])
def external_search():
    name = request.args.get("name", "").strip()
    if not name:
        return jsonify({"error": "name query parameter is required"}), 400
    try:
        products = search_products_by_name(name)
    except requests.RequestException as e:
        return jsonify({"error": f"External API error: {e}"}), 502
    return jsonify(products), 200


@app.route("/inventory/import", methods=["POST"])
def import_item():
    """Fetch a product from OpenFoodFacts (by barcode or name) and add it to inventory."""
    data = request.get_json(silent=True) or {}
    barcode, name = data.get("barcode"), data.get("name")
    if not barcode and not name:
        return jsonify({"error": "Provide 'barcode' or 'name'"}), 400
    try:
        if barcode:
            product = fetch_product_by_barcode(barcode)
        else:
            results = search_products_by_name(name)
            product = results[0] if results else None
    except requests.RequestException as e:
        return jsonify({"error": f"External API error: {e}"}), 502
    if not product:
        return jsonify({"error": "Product not found"}), 404
    product.update({"id": get_next_id(), "price": data.get("price", 0.0),
                    "stock": data.get("stock", 0)})
    inventory.append(product)
    return jsonify(product), 201


if __name__ == "__main__":
    app.run(debug=True)