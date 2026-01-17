# Objects API

A FastAPI project for managing objects.

## Run

```bash
uv run main.py
```

Server starts at `http://localhost:8000`

## POST Endpoint Test Data

**1. Gaming Console**
```json
{
   "name": "Sony PlayStation 5",
   "data": {
      "storage": "825 GB SSD",
      "color": "White",
      "price": 499.99,
      "edition": "Disc"
   }
}
```

**2. Headphones**
```json
{
   "name": "Sony WH-1000XM5",
   "data": {
      "type": "Over-ear",
      "noise_cancelling": true,
      "battery_life": "30 hours",
      "price": 349.99
   }
}
```

**3. Laptop**
```json
{
   "name": "Dell XPS 15",
   "data": {
      "processor": "Intel Core i7-13700H",
      "RAM": "32 GB",
      "display": "15.6 inch OLED",
      "price": 1899.00
   }
}
```

**4. Minimal (with null data)**
```json
{
   "name": "Generic USB-C Cable 2m"
}
```

## PUT Endpoint Test Data

PUT is a full update - provide both `name` and `data`.

**1. Update object id = 1 (Google Pixel 6 Pro)**
```json
{
   "name": "Google Pixel 8 Pro",
   "data": {
      "color": "Obsidian Black",
      "capacity": "256 GB",
      "price": 999.99,
      "chip": "Tensor G3"
   }
}
```

**2. Update object id = 6 (Apple AirPods)**
```json
{
   "name": "Apple AirPods Pro 2nd Gen",
   "data": {
      "chip": "H2",
      "price": 249.99,
      "noise_cancellation": true,
      "battery_life": "6 hours"
   }
}
```

## PATCH Endpoint Test Data

PATCH is a partial update - only provide fields you want to change.

**1. Update only name (id = 7)**
```json
{
   "name": "Apple MacBook Pro 16 (M3 Max)"
}
```

**2. Update only data (id = 5)**
```json
{
   "data": {
      "price": 599.99,
      "color": "Black",
      "condition": "Refurbished"
   }
}
```

**3. Update both (id = 9)**
```json
{
   "name": "Beats Studio Pro",
   "data": {
      "Color": "Sandstone",
      "price": 299.99
   }
}
```

## DELETE Endpoint Test Data

DELETE only needs the object ID in the URL - no request body.

- `DELETE /objects/6` - Deletes Apple AirPods
- `DELETE /objects/2` - Deletes Apple iPhone 12 Mini
- `DELETE /objects/13` - Deletes Apple iPad Air (256 GB)

Response:
```json
{
   "message": "Object with id = 6, has been deleted."
}
```
