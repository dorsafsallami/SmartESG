import io
import os
import time
import zipfile

import pandas as pd
import requests


def process_city_data(file_path, mun_file_path):
    try:
        # Read the CSV file containing census data
        census_df = pd.read_csv(file_path, encoding='ISO-8859-1')
        mun_df = pd.read_csv(mun_file_path)

        # Initialize an empty list to store the formatted DataFrames
        city_dfs = []

        # Iterate over each row in the mun_df DataFrame
        for index, row in mun_df.iterrows():
            city_name = row['munnom']
            
            # Filter the census DataFrame based on 'NIVEAU_GÉO' and 'NOM_GÉO'
            city_df = census_df[(census_df['NIVEAU_GÉO'] == row['NIVEAU_GÉO']) & 
                                (census_df['NOM_GÉO'] == row['NOM_GÉO'])]
            
            # Check if the filtered DataFrame is not empty
            if not city_df.empty:
                # Format the DataFrame by setting 'NOM_CARACTÉRISTIQUE' as the index and renaming the column
                formatted_city_df = city_df.set_index('NOM_CARACTÉRISTIQUE')['C1_CHIFFRE_TOTAL'].rename(city_name)
                
                # Append the formatted DataFrame to the list
                city_dfs.append(formatted_city_df)
            else:
                print(f"No data found for {city_name}")
        
        # Concatenate all formatted DataFrames into a single DataFrame
        if city_dfs:
            df_final = pd.concat(city_dfs, axis=1, sort=False)
            file_path = 'Recensement_de_la_population.csv'  # Replace with your desired file path
            df_final.to_csv(file_path, encoding='utf-8-sig')
        else:
            print("No data found for any city")
            return None
    
    except Exception as e:
        # Print any error messages
        print("Error processing the data:", e)
        return None

def download_and_process_census_data():
    """
    Downloads a ZIP file from the given URL, extracts its contents, processes the census data CSV,
    and calls the provided processing function.
    
    Args:
        url (str): The URL to download the ZIP file from.
        zip_path (str): Local path to save the ZIP file.
        extract_dir (str): Directory to extract the ZIP contents.
        csv_path (str): Path to the specific CSV file in the extracted data.
        mun_output_path (str): Path to save the processed city data.
        process_city_data_fn (callable): A function to process the city data.
    """
    # Start the timer
    start_time = time.time()
    url = 'https://www12.statcan.gc.ca/census-recensement/2021/dp-pd/prof/details/download-telecharger/comp/GetFile.cfm?Lang=F&FILETYPE=CSV&GEONO=005'
    # Local path to save the ZIP file
    zip_path = 'census_data.zip'

    try:
        # Download the ZIP file
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Save the ZIP file locally
        with open(zip_path, 'wb') as file:
            file.write(response.content)
        
        # Unzip the contents
        with zipfile.ZipFile(io.BytesIO(response.content)) as thezip:
            thezip.extractall('census_data')
        
        print(f"ZIP file successfully downloaded and extracted to census_data.")

        # Attempt to read the specified CSV file
        try:
            # Replace 'your_file.csv' with the path to your CSV file
            csv_path = 'census_data/98-401-X2021005_Francais_CSV_data.csv'

            # Read the CSV file into a DataFrame
            df = pd.read_csv(csv_path, encoding='ISO-8859-1')
            print(f"CSV file '{csv_path}' successfully loaded.")
        except Exception as e:
            print(f"Error reading the CSV file '{csv_path}':", e)
            return

        # Process the city data using the provided function
        mun_df = 'MUN.csv'
        process_city_data(csv_path, mun_df)

        # End the timer
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Process completed in {elapsed_time:.2f} seconds.")
    except requests.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")