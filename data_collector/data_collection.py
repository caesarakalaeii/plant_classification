from pygbif import species
import pandas as pd
import json

# JSON structure
data = {
    "plants": [],
    "plant_filter": {
        "number_of_plants": 5,
        "location": "",
        "cattle": []
    },
}
toxic_df = pd.read_csv("data/toxic_plant_DataV2.csv", sep=";")
toxic_plants = {}

def get_toxic_plants():
    for plant in toxic_df['Formal Botanical Name']:
        toxic_plants.update({plant: })


# Fetch plant data using pygbif
def fetch_plant_data(filter_criteria):
    # Search for plants (kingdom: Plantae)
    search_results = species.name_suggest(q="Plantae", rank="kingdom", limit=50)

    # Apply filters
    filtered_results = []
    for plant in search_results:
        if len(filtered_results) >= filter_criteria["number_of_plants"]:
            break
        # Example filter: by location (if applicable; adjust if using `occurrences` module for geolocation)
        if filter_criteria["location"]:
            # Note: pygbif occurrences can be used for specific geographic data
            continue
        filtered_results.append(plant)

    return filtered_results


# Filter criteria
filter_criteria = data["plant_filter"]

# Fetch and filter plant data
filtered_plants = fetch_plant_data(filter_criteria)

# Update JSON structure
data["plants"] = filtered_plants

# Display the results
print(json.dumps(data, indent=2))
