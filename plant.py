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