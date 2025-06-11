# main.py
import os
import re
import sys

import matplotlib.pyplot as plt
import numpy as np
import openai
import pandas as pd
from excel_parser import parse_data_files
from llm_agent import LLMAgent
from munesg_config import MetadataFramework
from preprocessor import ReportPreprocessor
from summarizer import summarize_text


def aggregate_category(category, indicators_info):
    """
    For a given category (e.g., "Environnement", "Social", "Gouvernance") and a list of tuples 
    (indicator, response), build a prompt to ask the LLM for an overall success percentage 
    for that category along with detailed scores for each indicator.
    """
    prompt = f"Vous êtes un expert en évaluation municipale. Voici les réponses détaillées pour la catégorie {category}:\n\n"
    for indicator, response in indicators_info:
        prompt += f"Indicateur: {indicator}\nRéponse: {response}\n\n"
    prompt += (
        "Veuillez fournir une estimation en pourcentage de la réussite globale de la municipalité "
        "dans cette catégorie (entre 0 et 100%), suivie d'une liste détaillée de chaque indicateur "
        "avec son score estimé. Le format doit être:\n\n"
        "Pourcentage global: XX%\nDétails:\n- Indicateur 1: XX%\n- Indicateur 2: XX%\n..."
    )
    system_prompt = "Vous êtes un expert en évaluation municipale fournissant des analyses détaillées."
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    return response['choices'][0]['message']['content']


    
def plot_category_scores_prev(data):
    categories = list(data.keys())
    values = [data[cat]["Pourcentage global"] for cat in categories]
    N = len(categories)

    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    width = 2 * np.pi / N

    fig, ax = plt.subplots(figsize=(10, 8), subplot_kw={'polar': True})

    # Use distinct colors (e.g., from tab10 colormap)
    colormap = plt.get_cmap("tab10")
    colors = [colormap(i % 10) for i in range(N)]

    bars = ax.bar(angles, values, width=width * 0.9, align='edge', edgecolor='black', linewidth=1.5)

    for i, (bar, angle, label, value) in enumerate(zip(bars, angles, categories, values)):
        bar.set_alpha(0.8)
        bar.set_linewidth(2)
        bar.set_facecolor(colors[i])
        rotation = np.degrees(angle + width / 2)
        alignment = 'left' if np.pi/2 < angle < 3*np.pi/2 else 'right'
        ax.text(
            angle + width / 2,
            value + 10,
            f'{label}\n{value}%',
            ha=alignment,
            va='center',
            rotation=rotation,
            rotation_mode='anchor',
            fontsize=12,
            fontweight='bold'
        )

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_yticklabels([])
    ax.set_xticks([])
    ax.set_title("Radial Bar Chart – Pourcentages Globaux par Catégorie", fontsize=16, fontweight='bold', y=1.1)
    plt.tight_layout()
    plt.show()

def plot_category_scores_prevv(data):
    categories = list(data.keys())
    values = [data[cat]["Pourcentage global"] for cat in categories]
    N = len(categories)

    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    width = 2 * np.pi / N

    fig, ax = plt.subplots(figsize=(10, 8), subplot_kw={'polar': True})

    colormap = plt.get_cmap("tab10")
    colors = [colormap(i % 10) for i in range(N)]

    bars = ax.bar(angles, values, width=width * 0.9, align='edge', edgecolor='black', linewidth=1.5)

    for i, (bar, angle, label, value) in enumerate(zip(bars, angles, categories, values)):
        bar.set_alpha(0.8)
        bar.set_linewidth(2)
        bar.set_facecolor(colors[i])
        rotation = np.degrees(angle + width / 2)
        alignment = 'left' if np.pi/2 < angle < 3*np.pi/2 else 'right'
        ax.text(
            angle + width / 2,
            value + 10,
            f'{label}\n{value}%',
            ha=alignment,
            va='center',
            rotation=rotation,
            rotation_mode='anchor',
            fontsize=12,
            fontweight='bold'
        )

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_yticklabels([])
    ax.set_xticks([])
    ax.set_title("Radial Bar Chart – Pourcentages Globaux par Catégorie", fontsize=16, fontweight='bold', y=1.1)
    plt.tight_layout()
    plt.show()

def plot_category_scores(data, output_file="category_scores.png"):
    categories = list(data.keys())
    values = [data[cat]["Pourcentage global"] for cat in categories]
    N = len(categories)

    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    width = 2 * np.pi / N

    fig, ax = plt.subplots(figsize=(10, 8), subplot_kw={'polar': True})

    colormap = plt.get_cmap("tab10")
    colors = [colormap(i % 10) for i in range(N)]

    bars = ax.bar(angles, values, width=width * 0.9, align='edge', edgecolor='black', linewidth=1.5)

    for i, (bar, angle, label, value) in enumerate(zip(bars, angles, categories, values)):
        bar.set_alpha(0.8)
        bar.set_linewidth(2)
        bar.set_facecolor(colors[i])
        rotation = np.degrees(angle + width / 2)
        alignment = 'left' if np.pi/2 < angle < 3*np.pi/2 else 'right'
        ax.text(
            angle + width / 2,
            value + 10,
            f'{label}\n{value}%',
            ha=alignment,
            va='center',
            rotation=rotation,
            rotation_mode='anchor',
            fontsize=12,
            fontweight='bold'
        )

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_yticklabels([])
    ax.set_xticks([])
    ax.set_title("Radial Bar Chart – Pourcentages Globaux par Catégorie", fontsize=16, fontweight='bold', y=1.1)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
def main():
    # Hardcoded configuration:
    folder = sys.argv[1]  # folder passed as argument

    query_all = True       # Set to True to query all indicators
    use_summarize = True   # Set to True to summarize long PDFs

    # Set your OpenAI API key here if not already set as an environment variable:
    openai.api_key = "put your key here"


    # Initialize metadata
    metadata = MetadataFramework()

    # Verify folder exists and list PDF files
    if not os.path.isdir(folder):
        print(f"Erreur : Le dossier '{folder}' n'existe pas.")
        sys.exit(1)
    pdf_files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print("Aucun fichier PDF trouvé dans le dossier.")
        sys.exit(1)

    # Process each PDF (and its associated Excel file)
    preprocessor = ReportPreprocessor()
    documents = []
    for pdf_file in pdf_files:
        print(f"[INFO] Traitement du PDF: {pdf_file}")
        try:
            raw_text = preprocessor.extract_text_from_pdf(pdf_file)
            if use_summarize:
                print(f"[INFO] Résumé du PDF: {pdf_file}")
                processed_text = summarize_text(raw_text)
            else:
                processed_text = raw_text
        except Exception as e:
            print(f"[ERROR] Échec de lecture du PDF {pdf_file}: {e}")
            processed_text = "[ERREUR DE LECTURE DU PDF]"

        # Look for an associated Excel file (same base name with .xlsx extension)
        base = os.path.splitext(os.path.basename(pdf_file))[0]
        excel_file = os.path.join(folder, base + ".xlsx")
        excel_text = ""
        if os.path.exists(excel_file):
            print(f"[INFO] Fichier Excel associé trouvé: {excel_file}")
            excel_text = parse_data_files([excel_file])
        else:
            print(f"[INFO] Aucun fichier Excel associé pour {pdf_file}")

        # Also include the census CSV (shared for all PDFs)
        csv_file = os.path.join(folder, "Recensement_de_la_population.csv")
        csv_text = ""
        if os.path.exists(csv_file):
            print(f"[INFO] Données CSV associées trouvées: {csv_file}")
            csv_text = parse_data_files([csv_file])
        else:
            print(f"[INFO] Aucun fichier CSV associé pour {pdf_file}")

        # Combine all parts into one document string
        combined_text = f"[PDF: {pdf_file}]\n{processed_text}\n"
        if excel_text.strip():
            combined_text += f"[Excel: {excel_file}]\n{excel_text}\n"
        if csv_text.strip():
            combined_text += f"[CSV: {csv_file}]\n{csv_text}\n"

        documents.append(combined_text)

    # Build the knowledge base using the LLM agent
    agent = LLMAgent()
    agent.build_knowledge_base(documents)

    # Query each indicator and store results by category
    category_results = {}  # Dictionary: key=category, value=list of (indicator, response)
    indicators = metadata.get_all_indicators()
    for ind in indicators:
        info = metadata.get_indicator_info(ind)
        query = f"{info['Indicateur']}. {info['Description']}"
        print(f"\n[INFO] Interrogation de l'LLM sur: {query}")
        answer = agent.answer_query(query)
        print(f"\n===== Réponse pour '{info['Indicateur']}' =====")
        print(answer)
        cat = info["Dimension"]
        if cat not in category_results:
            category_results[cat] = []
        category_results[cat].append((info["Indicateur"], answer))

    # Aggregate results by category and display overall success percentage and detailed scores
    """for cat, indicators_info in category_results.items():
        print(f"\n[INFO] Agrégation pour la catégorie '{cat}'")
        aggregated = aggregate_category(cat, indicators_info)
        print(f"\n===== Agrégation pour '{cat}' =====")
        print(aggregated)

        # Parse pourcentage global et scores détaillés à partir de la réponse texte
        score_match = re.search(r"Pourcentage global\s*:\s*(\d+)", aggregated)
        if score_match:
            global_score = int(score_match.group(1))
            details = dict(re.findall(r"- (.*?): (\d+)%", aggregated))
            details = {k.strip(): int(v) for k, v in details.items()}
            if 'aggregated_scores' not in locals():
                aggregated_scores = {}

            aggregated_scores[cat] = {
                "Pourcentage global": global_score,
                "Détails": details
            }
        
        # Après avoir rempli category_results pour tous, tracer le graphique
        plot_category_scores(aggregated_scores)
        """
        
    aggregated_scores = {}

    for cat, indicators_info in category_results.items():
        aggregated = aggregate_category(cat, indicators_info)

        # Parse pourcentage global et scores détaillés à partir de la réponse texte
        score_match = re.search(r"Pourcentage global\s*:\s*(\d+)", aggregated)
        if score_match:
            global_score = int(score_match.group(1))
            details = dict(re.findall(r"- (.*?): (\d+)%", aggregated))
            details = {k.strip(): int(v) for k, v in details.items()}

            aggregated_scores[cat] = {
            "Pourcentage global": global_score,
            "Détails": details
            }

    # Après avoir rempli category_results pour tous, tracer le graphique
    plot_category_scores(aggregated_scores, output_file="résultats_par_catégorie.png")
    
    # --- Prepare Sheet 1: Raw LLM Responses per Indicator ---
    llm_responses_data = []
    for category, indicators in category_results.items():
        for indicator, llm_response in indicators:
            llm_responses_data.append({
            "Catégorie": category,
            "Indicateur": indicator,
            "Réponse LLM": llm_response
            })

    df_responses = pd.DataFrame(llm_responses_data)

    # --- Prepare Sheet 2: Aggregated Category Scores ---
    aggregated_data = []
    for category, data in aggregated_scores.items():
        global_score = data["Pourcentage global"]
        for indicator, score in data["Détails"].items():
            aggregated_data.append({
            "Catégorie": category,
            "Indicateur": indicator,
            "Score de l'indicateur": score,
            "Score global de la catégorie": global_score
        })

    df_aggregated = pd.DataFrame(aggregated_data)

    # --- Write both to Excel file ---
    output_file = os.path.join(folder, "résultats_complets.xlsx")
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df_responses.to_excel(writer, index=False, sheet_name="Réponses LLM")
        df_aggregated.to_excel(writer, index=False, sheet_name="Scores Agrégés")

    print(f"\n[INFO] Résultats complets exportés vers : {output_file}")


    # Interface interactive human-in-the-loop
    print("\n[INFO] Interface interactive activée.")
    print("Vous pouvez maintenant poser des questions supplémentaires sur les indicateurs.")
    print("Tapez 'exit' pour quitter.\n")

    while True:
        user_question = input("Question ➤ ")
        if user_question.strip().lower() in ["exit", "quit", "q"]:
            print("Session terminée.")
            break
        response = agent.answer_query(user_question)
        print("\n🧠 Réponse de l'IA :\n")
        print(response)
        print("\n--- Posez une autre question ou tapez 'exit' pour quitter ---\n")

if __name__ == "__main__":
    main()
