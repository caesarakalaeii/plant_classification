class Plant:
    is_toxic: bool
    scientific_name: str
    gbif_key: str
    df_entry: int
    gbif_data: dict
    gbif_data_count: int


import os
import requests
from pygbif.occurrences import search

def pretty_print(input):
    for key, value in input.items():
        print(f'{key}: {value}')

def download_gbif_images_with_pygbif(plant_names, max_pictures, save_dir="gbif_images", country = "DE", months= [5], overwrite_file_name= None):
    """
    Downloads images associated with a plant name from GBIF using pygbif.

    Parameters:
        plant_names [str]: The scientific name of the plant.
        max_pictures (int): Maximum number of images to download per plant.
        save_dir (str): Directory to save the downloaded images.

    Returns:
        None
    """
    # Create the save directory if it does not exist
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    for a, plant_name in enumerate(plant_names):
        if overwrite_file_name is not None:
            if not os.path.exists(save_dir + "/" + overwrite_file_name):
                os.makedirs(save_dir + "/" + overwrite_file_name)
        else:
            if not os.path.exists(save_dir + "/" + plant_name):
                os.makedirs(save_dir + "/" + plant_name)
        for month in months:
            # Search for occurrences with media (images) using pygbif
            results = search(scientificName=plant_name, mediaType="StillImage", limit=int(max_pictures/len(months)), country=country, month=month)

            if not results.get("results"):
                print(f"No images found for plant: {plant_name}")
                return

            # Loop through the results to download images
            for i, record in enumerate(results["results"]):
                # pretty_print(record)
                media_items = record.get("media", [])
                if not media_items:
                    continue  # Skip records without media

                for media_item in media_items:
                    image_url = media_item.get("identifier")
                    if not image_url:
                        continue

                    # Download the image
                    try:
                        img_response = requests.get(image_url, stream=True)
                        img_response.raise_for_status()

                        # Save the image
                        file_extension = os.path.splitext(image_url)[-1] or ".jpg"
                        if file_extension not in [".jpg", ".jpeg", ".png", ]:
                            continue
                        if overwrite_file_name is None:
                            file_name = f"{plant_name.replace(' ', '_')}_{month}_{i+1}{file_extension}"
                            file_path = os.path.join(save_dir + "/" + plant_name, file_name)
                        else:
                            file_name = f"{plant_name.replace(' ', '_')}_{month}_{i+1}{file_extension}"
                            file_path = os.path.join(save_dir + "/" + overwrite_file_name, file_name)

                        with open(file_path, "wb") as img_file:
                            for chunk in img_response.iter_content(1024):
                                img_file.write(chunk)

                        print(f"Downloaded: {file_name}")
                    except requests.RequestException as e:
                        print(f"Failed to download image: {image_url}. Error: {e}")
                        continue

# Example usage
# download plants to classify
download_gbif_images_with_pygbif(["Jacobaea vulgaris", "Digitalis L.", "Colchicum autumnale L."], 160, country="DE", months=[4,5,6,7,8])
# Download Filler plants
download_gbif_images_with_pygbif(["Achillea millefolium", "Fagus sylvatica", "Corylus avellana", "Quercus robur", "Urtica dioica", "Hedera helix", "Sambucus nigra", "Acer pseudoplatanus", "Glechoma hederacea", "Plantago lanceolata", "Ranunculus repens"], 20, country="DE", months=[4,5,6,7,8], overwrite_file_name="no_class")