import json
import os
import re
import time

import pandas as pd
import PyPDF2
import tiktoken
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import TokenTextSplitter
from langchain_core.messages import HumanMessage, SystemMessage
from tenacity import retry, stop_after_attempt, wait_exponential

# Configuration
openai_api_key = "put your key here"  
model = ChatOpenAI(model="gpt-4", temperature=0, openai_api_key=openai_api_key)

# Liste COMPLÈTE de vos keywords (à inclure dans le prompt)
CO2e = [
    "CO2", "éq. C0", "t CO2e", "TéqCO2", "téq. CO2", "Mt CO2e", "Mt éq. CO2", "tonnes équivalentes de CO2", 
    "tonnes éq. de CO2", "tonnes de CO2", "CO2 équivalent", "kt éq. CO2", 
    "kt CO2e", "tonnes métriques de CO2", "tonnes métriques équivalentes de CO2", 
    "Inventaire GES", "Émissions de GES", "Scope 1", "Scope 2", "Scope 3", 
    "Émissions totales", "Global Protocol for Community-Scale Greenhouse Gas Emissions Inventories", 
    "GPC", "CDP", "ISO 37120", "ISO 37122", "ISO 37123", "TCFD", 
    "Task Force on Climate-related Financial Disclosure", "Groupe de travail sur l’information financière relative aux changements climatiques", 
    "GIFCC", "C40", "ICLEI", "Nombre d’actions climatiques", "Nbr d’actions", 
    "Cible 2030", "Cible 2050", "Cible d’adaptation climatique", "cible d’atténuation climatique", 
    "cible de réduction des émissions", "cible climat", "cible climatique", "Plan climat", 
    "scénario climatique", "scénarios climatiques", "budget carbone", "budget climat", 
    "plan d’atténuation climatique", "résilience climatique", "vulnérabilité climatique", 
    "Estimation des émissions sauvées", "estimation des émissions réduites", 
    "estimations des émissions"
]
natural_gas_keywords = [
    "Gaz naturel", "m3 de gaz naturel", "millions de m3", "litres d’essence", 
    "l d’essence", "millions de litres", "consommation de combustibles fossiles", 
    "essence", "diésel", "mazout léger", "propane", "énergie renouvelable", 
    "énergie générée", "génération d’énergie", "génération annuelle d’énergie", 
    "estimation de l’énergie sauvé"
]
energy_keywords = [
    "MWh", "GWh", "consommation totale d’énergie", "kWh par année par personne",
    "kWh par année par habitant", "Consommation énergétique",
    "estimation de l’énergie sauvé", "estimation annuelle de l’énergie sauvé"
]
waste_keywords = [
    "Tonnes de déchets", "montant total de déchets", "t de déchets", "% total de déchets",
    "pourcentage total de déchets", "volume d’eaux usées traitées", "pourcentage d’eaux usées traitées",
    "Traitement des déchets", "traitement des déchets organiques", "traitement des eaux usées"
]
transport_keywords = [
    "Pourcentage de passager par mode de transport", "% de passager par mode de transport",
    "pourcentage par mode de transport", "% par mode de transport",
    "pourcentage de véhicules électriques", "% de véhicules électriques",
    "pourcentage d’autobus électrique", "% d’autobus électriques",
    "pourcentage d’autobus électrifiés", "% d’autobus électrifiés",
    "transport en commun", "transport collectif", "électrification des transports",
    "électrification de la flotte automobile", "borne de recharges électriques"
]
heat_island_keywords = [
    "Superficie des îlots de chaleur"
]
aires_keywords = [
    "Superficie des aires protégées", "superficie d’aires protégées", "superficie du territoire en aires protégées", 
    "% du territoire en aires protégées", "pourcentage du territoire en aires protégées"
]
smog_keywords = [
    "Pourcentage annuel de jours sans smog", "% annuel de jours sans smog", "nombre de jours sans smog", 
    "Indice de qualité de l’air", "indice annuel de la qualité de l’air", "températures moyennes annuelles"
]
inondable_keywords = [
    "Km2 de zone inondable", "km2 de zones inondables"
]
batiments_keywords = [
    "Nbr de bâtiments verts", "m2 de bâtiments verts", "nbr de bâtiments zéro carbone", 
    "nbr de bâtiments municipaux zéro carbone", "m2 de bâtiments zéro carbone", 
    "m2 de bâtiments municipaux zéro carbone"
]
logements_keywords = [
    "Logements abordables", "infrastructures vertes"
]

# Combine them into a dictionary
keywords_unite_dict = {
    'CO2e': CO2e,
    'natural_gas_keywords': natural_gas_keywords,
    'energy_keywords': energy_keywords,
    'waste_keywords': waste_keywords,
    'transport_keywords': transport_keywords,
    'heat_island_keywords': heat_island_keywords,
    'aires_keywords': aires_keywords,
    'smog_keywords': smog_keywords,
    'inondable_keywords': inondable_keywords,
    'batiments_keywords': batiments_keywords,
    'logements_keywords': logements_keywords
}

# Define the system prompt with instructions.
system_prompt = SystemMessage(content=f"""
Tu es un expert en extraction de données quantitatives.

Consignes :
1. Pour chaque catégorie prédéfinie (CO2e, énergie, déchets, etc.) :
{keywords_unite_dict}
2. Pour chaque mot-clé de chaque catégorie :
   - Si détection avec valeur numérique → retourne: catégorie, mot_cle, valeur, unité, contexte
   - Si détection sans valeur → retourne: catégorie, mot_cle, valeur=null, unité=notfound, contexte=notfound
3. Extract ALL keyword occurrences with their context. Keep duplicates with different contexts.


**Format de sortie attendu** :
```json
{{
  "donnees": [
    {{
      "categorie": "CO2e",
      "mot_cle": "t CO2e",
      "valeur": 1200.5,
      "unite": "t CO2e",
      "contexte": "Réduction de 1200.5 t CO2e en 2023 (Scope 1)"
    }},
    {{
      "categorie": "CO2e",
      "mot_cle": "Scope 3",
      "valeur": null,
      "unite": "notfound",
      "contexte": "notfound"
    }}
  ]
}}
""")

# ====================== PDF Reading Function ======================
def read_pdf(pdf_path):
    """Extract text from PDF with OCR fallback"""
    try:
        text = ""
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""  # Handle None returns
            
        # Fallback to OCR if text extraction fails
        if len(text.strip()) < 100:
            try:
                import pytesseract
                from pdf2image import convert_from_bytes
                images = convert_from_bytes(open(pdf_path, "rb").read())
                text = "\n".join([pytesseract.image_to_string(img) for img in images])
            except ImportError:
                print("Install pdf2image and pytesseract for OCR support")
                
        return text
    
    except Exception as e:
        print(f"PDF reading error: {str(e)}")
        return ""
def extract_keyword_values(pdf_path):
    """Main processing pipeline with context-aware deduplication"""
    text = read_pdf(pdf_path)
    chunks = TokenTextSplitter(chunk_size=4000, chunk_overlap=500).split_text(text)
    
    all_results = []
    for idx, chunk in enumerate(chunks):
        print(f"Processing chunk {idx+1}/{len(chunks)}")
        result = process_chunk(chunk)
        if result and 'donnees' in result:
            all_results.extend(result['donnees'])
        time.sleep(0.5)
    
    return pd.DataFrame(all_results).drop_duplicates(
        subset=['categorie', 'mot_cle', 'contexte'],
        keep='first'
    )

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=20))
def process_chunk(chunk):
    """Process text chunk with GPT-4"""
    try:
        response = model.invoke([
            SystemMessage(content=f"""
            Tu es un expert en extraction de données quantitatives.

Consignes :
1. Pour chaque catégorie prédéfinie (CO2e, énergie, déchets, etc.) :
{keywords_unite_dict}
2. Pour chaque mot-clé de chaque catégorie :
   - Si détection avec valeur numérique → retourne: catégorie, mot_cle, valeur, unité, contexte
   - Si détection sans valeur → retourne: catégorie, mot_cle, valeur=null, unité=notfound, contexte=notfound
3. Extract ALL keyword occurrences with their context. Keep duplicates with different contexts.


**Format de sortie attendu** :
```json
{{
  "donnees": [
    {{
      "categorie": "CO2e",
      "mot_cle": "t CO2e",
      "valeur": 1200.5,
      "unite": "t CO2e",
      "contexte": "Réduction de 1200.5 t CO2e en 2023 (Scope 1)"
    }},
    {{
      "categorie": "CO2e",
      "mot_cle": "Scope 3",
      "valeur": null,
      "unite": "notfound",
      "contexte": "notfound"
    }}
  ]
}}
"""),
            HumanMessage(content=f"Texte:\n{chunk[:6000]}")
        ])
        return parse_response(response)
    except Exception as e:
        print(f"Chunk processing error: {str(e)}")
        return None

def parse_response(response):
    """Improved JSON parsing"""
    try:
        # Handle various JSON formats
        json_str = re.sub(r'[\x00-\x1F]+', '', response.content)  # Remove control characters
        match = re.search(r'\{.*\}', json_str, re.DOTALL)
        if match:
            return json.loads(match.group())
        return None
    except (AttributeError, json.JSONDecodeError) as e:
        print(f"JSON parsing error: {str(e)}")
        return None


def main(folder_path):
    all_results = []

    for file in os.listdir(folder_path):
        if file.lower().endswith(".pdf"):
            pdf_path = os.path.join(folder_path, file)
            print(f"🔍 Traitement du fichier : {pdf_path}")
            df = extract_keyword_values(pdf_path)
            df["fichier"] = file
            all_results.append(df)

    final_df = pd.concat(all_results, ignore_index=True)
    output_path = os.path.join(folder_path, "résultats_quantitatifs_text.csv")
    final_df.to_csv(output_path, index=False)
    print(f"✅ Extraction terminée. Résultats enregistrés dans : {output_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        folder = sys.argv[1]
        main(folder)
    else:
        print("❌ Argument de dossier manquant.")
