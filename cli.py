import argparse
import json
import os
import requests

BASE_URL = os.environ.get("API_URL", "http://127.0.0.1:5000")


def show(resp):
    try:
        print(json.dumps(resp.json(), indent=2))
    except ValueError:
        print(resp.text)


def main():
    parser = argparse.ArgumentParser(description="Inventory Management CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List all items")

    p = sub.add_parser("get", help="Get one item")
    p.add_argument("id", type=int)

    p = sub.add_parser("add", help="Add an item")
    p.add_argument("name")
    p.add_argument("--brand", default="")
    p.add_argument("--barcode", default="")
    p.add_argument("--price", type=float, default=0.0)
    p.add_argument("--stock", type=int, default=0)

    p = sub.add_parser("update", help="Update an item")
    p.add_argument("id", type=int)
    p.add_argument("--name")
    p.add_argument("--brand")
    p.add_argument("--price", type=float)
    p.add_argument("--stock", type=int)

    p = sub.add_parser("delete", help="Delete an item")
    p.add_argument("id", type=int)

    p = sub.add_parser("lookup", help="Look up product on OpenFoodFacts by barcode")
    p.add_argument("barcode")

    p = sub.add_parser("search", help="Search OpenFoodFacts by name")
    p.add_argument("name")

    p = sub.add_parser("import", help="Import from OpenFoodFacts into inventory")
    p.add_argument("--barcode")
    p.add_argument("--name")
    p.add_argument("--price", type=float, default=0.0)
    p.add_argument("--stock", type=int, default=0)

    a = parser.parse_args()

    try:
        if a.command == "list":
            r = requests.get(f"{BASE_URL}/inventory")
        elif a.command == "get":
            r = requests.get(f"{BASE_URL}/inventory/{a.id}")
        elif a.command == "add":
            r = requests.post(f"{BASE_URL}/inventory", json={
                "product_name": a.name, "brands": a.brand, "barcode": a.barcode,
                "price": a.price, "stock": a.stock})
        elif a.command == "update":
            body = {k: v for k, v in {"product_name": a.name, "brands": a.brand,
                                      "price": a.price, "stock": a.stock}.items() if v is not None}
            r = requests.patch(f"{BASE_URL}/inventory/{a.id}", json=body)
        elif a.command == "delete":
            r = requests.delete(f"{BASE_URL}/inventory/{a.id}")
        elif a.command == "lookup":
            r = requests.get(f"{BASE_URL}/external/barcode/{a.barcode}")
        elif a.command == "search":
            r = requests.get(f"{BASE_URL}/external/search", params={"name": a.name})
        elif a.command == "import":
            r = requests.post(f"{BASE_URL}/inventory/import", json={
                "barcode": a.barcode, "name": a.name, "price": a.price, "stock": a.stock})
        show(r)
    except requests.ConnectionError:
        print("Could not connect to the API. Is the Flask server running (python app.py)?")


if __name__ == "__main__":
    main()