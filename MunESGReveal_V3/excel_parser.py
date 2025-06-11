# excel_parser.py
import os

import pandas as pd


def parse_data_files(file_paths):
    """
    Reads Excel or CSV files and converts them to text for LLM consumption.
    """
    combined_text = ""
    for path in file_paths:
        if not os.path.exists(path):
            print(f"Attention: Fichier introuvable: {path}")
            continue

        ext = os.path.splitext(path)[1].lower()
        try:
            if ext == ".csv":
                df = pd.read_csv(path)
            elif ext in [".xls", ".xlsx"]:
                df = pd.read_excel(path)
            else:
                print(f"Format non supporté: {path}")
                continue

            text_data = df.to_csv(index=False)
            combined_text += f"\n[DATA: {path}]\n{text_data}\n"
        except Exception as e:
            print(f"Erreur de lecture pour {path} : {e}")
    return combined_text

