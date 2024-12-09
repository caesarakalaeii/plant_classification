class PLant:
    is_toxic: bool
    scientific_name: str
    gbif_key: str
    df_entry: int
    gbif_data: dict
    gbif_data_count: int

    #TODO: Add functions to generate data on the fly
    # 1. fetch data from data frame
    # 2. fetch key from GBIF
    # 3. fetch data from GBIF
    # 4. add functionality for comparison


import os
import requests
from pygbif.occurrences import search

def download_gbif_images_with_pygbif(plant_name, max_pictures, save_dir="gbif_images"):
    """
    Downloads images associated with a plant name from GBIF using pygbif.

    Parameters:
        plant_name (str): The scientific name of the plant.
        max_pictures (int): Maximum number of images to download.
        save_dir (str): Directory to save the downloaded images.

    Returns:
        None
    """
    # Create the save directory if it does not exist
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # Search for occurrences with media (images) using pygbif
    results = search(scientificName=plant_name, mediaType="StillImage", limit=max_pictures)

    if not results.get("results"):
        print(f"No images found for plant: {plant_name}")
        return

    # Loop through the results to download images
    for i, record in enumerate(results["results"]):
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
                file_name = f"{plant_name.replace(' ', '_')}_{i+1}{file_extension}"
                file_path = os.path.join(save_dir, file_name)

                with open(file_path, "wb") as img_file:
                    for chunk in img_response.iter_content(1024):
                        img_file.write(chunk)

                print(f"Downloaded: {file_name}")
            except requests.RequestException as e:
                print(f"Failed to download image: {image_url}. Error: {e}")

# Example usage
download_gbif_images_with_pygbif("Rosa rubiginosa", 5)
