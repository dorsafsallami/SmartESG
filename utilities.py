import datetime
import os

import pandas as pd


def get_folder_creation_time(folder_path):
    try:
        # Get the creation time in seconds
        creation_time = os.path.getctime(folder_path)
        
        # Convert to a datetime object
        creation_datetime = datetime.datetime.fromtimestamp(creation_time)
        
        return creation_datetime.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        return f"Error: {e}"

def get_file_creation_time(input_excel_path):
    try:
        # Check if the file exists
        if not os.path.exists(input_excel_path):
            return f"Error: The file '{input_excel_path}' does not exist."

        # Get the creation time of the file
        creation_time = os.path.getctime(input_excel_path)
        
        # Convert to a human-readable datetime format
        creation_datetime = datetime.datetime.fromtimestamp(creation_time)
        
        # Return the formatted creation date
        return creation_datetime.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        return f"Error: {e}"

    
def get_folder_statistics(folder_path):
    # Dictionary to hold statistics
    stats = {
        "total_subfolders": 0,
        "subfolders": {}
    }

    # Walk through the directory
    for root, dirs, files in os.walk(folder_path):
        # Only consider the immediate subfolders, ignore nested sub-subfolders
        if root == folder_path:
            stats["total_subfolders"] = len(dirs)
            for subfolder in dirs:
                subfolder_path = os.path.join(root, subfolder)
                
                # Count PDF files in each subfolder
                pdf_count = sum(1 for file in os.listdir(subfolder_path) if file.lower().endswith('.pdf'))
                
                # Add data to stats dictionary
                stats["subfolders"][subfolder] = {
                    "pdf_count": pdf_count
                }

    return stats
# Function to save data to an existing CSV
def save_to_csv(data, file_path):
    try:
        # Load the existing data
        df = pd.read_csv(file_path)
        # Append new data
        df = df.append(data, ignore_index=True)
        # Save back to CSV
        df.to_csv(file_path, index=False)
        return "Enregistré avec succès !"
    except Exception as e:
        return f"Error: {e}"

def load_data(path_to_your_csv):
    df = pd.read_csv(path_to_your_csv)
    return df


# Define a function to construct the file path based on the selected options
def construct_file_path(municipality, analysis_type):
    base_directory = 'C:/Users/dorsa/Documents/Mitacs-2024-2025/Code/Final Code/pdfs_downloaded_filter'
    if analysis_type == "Par mot-clé":
        file_name = "aggregated_category_keyword_counts_sentiments.xlsx"
    elif analysis_type == "Par fichiers":
        file_name = "aggregated_keyword_counts_by_file_nbPage.xlsx"
    elif analysis_type == "Par mot-clé et sentiment":
        file_name = "aggregated_category_keyword_sentiment_score.xlsx"
    return os.path.join(base_directory, municipality, file_name)

# Define a function to construct the file path based on the selected options
def construct_file_path_analyse(municipality):
    base_directory = 'C:/Users/dorsa/Documents/Mitacs-2024-2025/Code/Final Code/pdfs_downloaded_filter'
    file_name = "aggregated_category_keyword_counts_sentiments.xlsx"
    return os.path.join(base_directory, municipality, file_name)


def load_analysis_results(file_path):
    if os.path.exists(file_path):
        return pd.read_excel(file_path)
    else:
        return pd.DataFrame()