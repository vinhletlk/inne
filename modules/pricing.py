def calculate_price(mass_grams, tech, material):
    price_table = {
        ("FDM", "PLA"): 1000,
        ("FDM", "ABS"): 1200,
        ("Resin", "Resin"): 3000
    }
    key = (tech, material)
    price_per_g = price_table.get(key, 1000)
    price = int(mass_grams * price_per_g)
    return {
        "price": price,
        "tech": tech,
        "material": material
    }
