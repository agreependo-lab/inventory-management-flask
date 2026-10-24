# Inventory Management System (Flask REST API)

A Flask REST API for managing retail inventory, with OpenFoodFacts integration and a CLI.

## Features
- CRUD for inventory items (in-memory storage)
- Fetch product details from the OpenFoodFacts API by barcode or name and import them into inventory
- CLI to interact with the API
- Unit tests (pytest, external API mocked)

## Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```
Server runs at http://127.0.0.1:5000.

## API Endpoints
| Method | Endpoint | Description |
|---|---|---|
| GET | /inventory | List all items |
| GET | /inventory/<id> | Get one item |
| POST | /inventory | Create item (`product_name` required) |
| PATCH | /inventory/<id> | Update item fields |
| DELETE | /inventory/<id> | Delete item |
| GET | /external/barcode/<barcode> | Look up product on OpenFoodFacts |
| GET | /external/search?name=... | Search OpenFoodFacts by name |
| POST | /inventory/import | Import from OpenFoodFacts (`barcode` or `name`, optional `price`, `stock`) |

## CLI (run the server in another terminal first)
```bash
python cli.py list
python cli.py get 1
python cli.py add "Oats" --brand Quaker --price 2.5 --stock 10
python cli.py update 1 --price 4.99 --stock 30
python cli.py delete 2
python cli.py lookup 3017620422003
python cli.py search nutella
python cli.py import --barcode 3017620422003 --price 6.5 --stock 20
```

## Tests
```bash
pytest -v
```

## Design
Single Flask app (`app.py`) with helper functions for the external API, a `cli.py` that calls the API with `requests`, and `test_app.py` with pytest using a mocked external API.