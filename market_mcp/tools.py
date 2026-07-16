import json


def load_market_data():
    with open("market_data.json", "r") as file:
        return json.load(file)


def load_scheme_data():
    with open("schemes.json", "r") as file:
        return json.load(file)


def market_price(crop_name: str):
    data = load_market_data()
    crop = data.get(crop_name.lower().strip())
    if not crop:
        return f"No market data found for {crop_name}"

    return {
        "crop": crop_name,
        "price": crop["price"],
        "trend": crop["trend"]
    }


def government_scheme(farmer_type: str):
    data = load_scheme_data()

    scheme = data.get(farmer_type.lower().strip())

    if not scheme:
        return f"No scheme found for {farmer_type}"

    return scheme


def best_selling_crop():
    data = load_market_data()

    sorted_crops = sorted(
        data.items(),
        key=lambda x: x[1]["price"],
        reverse=True
    )

    return [crop[0] for crop in sorted_crops[:3]]


def profit_calculator(crop_name: str, quantity: int):
    data = load_market_data()

    crop = data.get(crop_name.lower().strip())

    if not crop:
        return f"No market data found for {crop_name}"

    revenue = crop["price"] * quantity

    return {
        "crop": crop_name,
        "quantity": quantity,
        "price_per_kg": crop["price"],
        "revenue": revenue
    }