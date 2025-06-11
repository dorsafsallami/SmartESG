import os
import shutil
import time

import pandas as pd
import streamlit as st

from analysis import process_pdfs_in_folder
from downloadQuali import download_pdfs_from_url
from downloadQuanti import download_and_process_census_data
from utilities import (construct_file_path, construct_file_path_analyse,
                       get_file_creation_time, get_folder_creation_time,
                       get_folder_statistics, load_analysis_results, load_data,
                       save_to_csv)


def plot_category_scores(df):
    categories = df['Catégorie'].unique()
    scores = df.groupby('Catégorie')["Score global de la catégorie"].first().tolist()

    N = len(categories)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    width = 2 * np.pi / N

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={'polar': True})
    colormap = plt.get_cmap("tab10")
    colors = [colormap(i % 10) for i in range(N)]

    bars = ax.bar(angles, scores, width=width * 0.9, align='edge', edgecolor='black', linewidth=1.5)

    for i, (bar, angle, label, value) in enumerate(zip(bars, angles, categories, scores)):
        bar.set_alpha(0.8)
        bar.set_facecolor(colors[i])
        rotation = np.degrees(angle + width / 2)
        align = 'left' if np.pi/2 < angle < 3*np.pi/2 else 'right'
        ax.text(angle + width / 2, value + 5, f"{label}\n{value}%", ha=align, va='center',
                rotation=rotation, rotation_mode='anchor', fontsize=10, fontweight='bold')

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_yticklabels([])
    ax.set_xticks([])
    ax.set_title("Scores par Catégorie", fontsize=14, fontweight='bold', y=1.1)
    st.pyplot(fig)

# Custom CSS to hide radio button circles and style the options as full-width clickable links
st.markdown("""
    <style>
        .stRadio > div {flex-direction: column;} /* Stack options vertically */
        .stRadio > label {display: none;} /* Hide radio button labels */
        
        .stRadio div[data-baseweb="radio"] > div {
            background-color: #f0f2f6;
            border-radius: 5px;
            margin: 5px 0;
            padding: 10px;
            text-align: center;
            font-size: 1.1em;
            cursor: pointer;
            color: #333;
            width: 100%;
            display: inline-block;
        }
        
        .stRadio div[data-baseweb="radio"] > div:hover {
            background-color: #e0e4e8;
        }
        
        /* Highlight selected option */
        .stRadio div[data-baseweb="radio"] > div[aria-checked="true"] {
            background-color: #FF4B4B;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# Sidebar title and navigation options using st.radio
st.sidebar.title("Smart ESG")

# Displaying radio buttons as navigation options
section = st.sidebar.radio("Go to:", ["À propos", "Télécharger", "Analyse",  "Analyse avancée", "MunESGReveal"])

# Define the layout for each section based on the selected option
if section == "À propos":
    st.title("À propos")
    st.markdown("""
        <div style="text-align: justify; font-size: 1.1em;">
                Le projet Smart ESG vise à révolutionner la manière dont les entreprises abordent leurs objectifs Environnementaux, Sociaux et de Gouvernance (ESG)
                en intégrant des solutions avancées d'Intelligence Artificielle. En utilisant l'IA pour analyser en temps réel les données ESG, Smart ESG permet une 
                transparence accrue, une conformité automatisée et des insights prédictifs pour anticiper les risques et maximiser l'impact positif. 
                Notre solution aide les entreprises à naviguer dans les défis actuels de durabilité et de responsabilité, leur offrant une gestion optimisée et des décisions
                éclairées pour un avenir plus vert et éthique..
        </div>
    """, unsafe_allow_html=True)

elif section == "Télécharger":
    st.title("Télécharger")
    # Call the function to get the last downloaded time
    folder_path = "C:/Users/dorsa/Documents/Mitacs-2024-2025/Code/Final Code/Interface/pdfs_downloaded_filter"
    last_download_time = get_folder_creation_time(folder_path)
    # Display the last downloaded time
    st.write(f"Dernière date de téléchargement : {last_download_time}")

    # Subsection 1: Last Download Information
    with st.expander("Statistiques sur le Dernier Téléchargement"):
        # Call the function to get folder statistics
        folder_stats = get_folder_statistics(folder_path)

        # Display the folder statistics
        st.write(f"Total des municipalités: {folder_stats['total_subfolders']}")
        for subfolder, stats in folder_stats['subfolders'].items():
            st.write(f"- {subfolder}: {stats['pdf_count']} PDFs")


    # Subsection 2: Folder Statistics
    with st.expander("Ajouter une municipalité"):
        st.write("Voulez-vous ajouter une municipalité ?")
        # Create a form for new data input
        with st.form(key='municipality_form'):
            munnom = st.text_input("Nom de la municipalité")
            niveau_geo = st.text_input("Niveau Géographique")
            nom_geo = st.text_input("Nom Géographique")
            mweb = st.text_input("Site Web Municipal")
            
            # Form submission button
            submit_button = st.form_submit_button("Enregistrer dans CSV")
        
        if submit_button:
            if not munnom or not mweb:  # Check if obligatory fields are empty
                st.error("Les champs 'Nom de la municipalité' et 'Site Web Municipal' sont obligatoires.")
            else:
                new_data = {
                'munnom': munnom,
                'NIVEAU_GÉO': niveau_geo,
                'NOM_GÉO': nom_geo,
                'mweb': mweb
            }
            
            # Call the function to save data to CSV
            result = save_to_csv(new_data, 'MUN.csv')
            st.write(result)
    
    # Subsection 3: telechargement pdfs pour une muni
    with st.expander("Voulez-vous télécharger les documents pour une municipalité?"):
        df = load_data('MUN.csv')
        unique_municipalities = df['munnom'].unique()
        selected_municipality = st.selectbox("Choisissez une municipalité", unique_municipalities)
        # Perform analysis based on selection
        if st.button("Télécharger"):
            keywords = ['rapport', 'annuel', 'plan', 'stratégie', 'finance', 'urbanisme', 'budget', 'politique', 'bilan']
            # Filter the DataFrame for the selected municipality
            filtered_row = df[df['munnom'] == selected_municipality]

            if not filtered_row.empty:
                # Extract the 'mweb' column value for the selected municipality
                mweb_value = filtered_row.iloc[0]['mweb']
    
                # Construct the mweb_url based on the condition
                mweb_url = 'https://' + mweb_value if not mweb_value.startswith('http') else mweb_value
    
                print(f"The mweb_url for {selected_municipality} is: {mweb_url}")
            else:
                print(f"No data found for the municipality: {selected_municipality}")
            
            print(f"Start downloading for {selected_municipality}")
            st.write(f"Début du téléchargement pour {selected_municipality}...")
            munnom_directory = f'pdfs_downloaded_filter/{selected_municipality}'
            # Ensure the save directory exists
            if not os.path.exists(munnom_directory):
                os.makedirs(munnom_directory)
            st.write(f"Directory set to: {munnom_directory}")
            
            visited_urls = set()
            skipped_files_info = []
            downloaded_pdfs = set()
            start_time = time.time()
            download_pdfs_from_url(munnom, mweb_url, munnom_directory, visited_urls, downloaded_pdfs, skipped_files_info, keywords)
            print(f"Time taken for {munnom}: {time.time() - start_time} seconds")

            df_skipped = pd.DataFrame(skipped_files_info)
            excel_file_path = os.path.join(munnom_directory, 'skipped_files_info.xlsx')
            df_skipped.to_excel(excel_file_path, index=False)
            st.write(f"Téléchargement terminé pour {selected_municipality}!")
            st.write(f"Temps écoulé pour {munnom}: {time.time() - start_time} secondes")

    # Subsection 4: telechargement pdfs
    with st.expander("Voulez-vous retélécharger les documents?"):
        # Option to re-download fewer documents
        st.write("Voulez-vous retélécharger les documents ?")

        # Button to trigger download
        if st.button("Retélécharger"):
            excel_path = 'MUN.csv'
            df = pd.read_csv(excel_path)
            keywords = ['rapport', 'annuel', 'plan', 'stratégie', 'finance', 'urbanisme', 'budget', 'politique', 'bilan']
        
            for index, row in df.iterrows():
                skipped_files_info = []
                munnom = row['munnom']
                mweb_url = 'https://' + row['mweb'] if not row['mweb'].startswith('http') else row['mweb']
    
                print(f"Start downloading for {munnom}")
                st.write(f"Début du téléchargement pour {munnom}")

                munnom_directory = f'pdfs_downloaded_filter/{row["munnom"]}'  # Directory name based on 'munnom' column

                if os.path.exists(munnom_directory):
                    # Delete the existing directory
                    shutil.rmtree(munnom_directory)
                    # Create a new empty directory
                    os.makedirs(munnom_directory)

                visited_urls = set()
                downloaded_pdfs = set()
                start_time = time.time()
                download_pdfs_from_url(munnom, mweb_url, munnom_directory, visited_urls, downloaded_pdfs, skipped_files_info, keywords)
                print(f"Time taken for {munnom}: {time.time() - start_time} seconds")
                
                st.write(f"Téléchargement terminé pour {munnom}")
                st.write(f"Temps écoulé pour {munnom}: {time.time() - start_time} secondes")

                df_skipped = pd.DataFrame(skipped_files_info)
                excel_file_path = os.path.join(munnom_directory, 'skipped_files_info.xlsx')
                df_skipped.to_excel(excel_file_path, index=False)

    # Subsection 5: telechargement donnees quantitatives
    with st.expander("Voulez-vous retélécharger les données  quantitatives?"):
        st.write("Voulez-vous retélécharger les données  quantitatives?")
        # Button to trigger download
        if st.button("Retélécharger les données  quantitatives"):
            st.write(f"Début du téléchargement")
            download_and_process_census_data()
            st.write(f"Téléchargement terminé")
        
    

elif section == "Analyse":
    st.title("Analyse")
    with st.expander("Dernière date d'analyse"):
        # Call the function to get the last downloaded time
        folder_path = "C:/Users/dorsa/Documents/Mitacs-2024-2025/Code/Final Code/pdfs_downloaded_filter"
        df = load_data('MUN.csv')
        unique_municipalities = df['munnom'].unique()
        for municipality in unique_municipalities:
            file_path = construct_file_path_analyse(municipality)
            last_analyse_time = get_file_creation_time(file_path)
            # Display the last downloaded time
            st.write(f"Dernière date d'analyse pour {municipality} : {last_analyse_time}")


    with st.expander("Afficher analyse par Municipalité"):
        df = load_data('MUN.csv')
        unique_municipalities = df['munnom'].unique()
        selected_municipality = st.selectbox("Choisissez une municipalité", unique_municipalities)

        # Dropdown for selecting type of analysis
        analysis_types = ["Par mot-clé", "Par fichiers", "Par mot-clé et sentiment"]
        selected_analysis = st.selectbox("Choisissez le type d'agrégation", analysis_types, format_func=lambda x: x)

        # Placeholder for displaying analysis results
        result_placeholder = st.empty()

        # Perform analysis based on selection
        if st.button("Afficher les Résultats"):
            file_path = construct_file_path(selected_municipality, selected_analysis)
            results = load_analysis_results(file_path)
            if not results.empty:
                st.write("Résultats d'analyse :")
                st.dataframe(results)
            else:
                st.write("Aucun résultat trouvé pour les critères sélectionnés.")
    
    with st.expander("Afficher mots-clés utilisés pour l'analyse"):
        uploaded_file = "keywords_category.csv"  # Chemin du fichier téléchargé
        df = pd.read_csv(uploaded_file, encoding='utf-8-sig')

        st.subheader("Catégories et Mots-Clés Existants")
        st.write("Modifiez directement les valeurs dans le tableau ci-dessous :")

        # Display an editable table
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

        # Save the modified data to the file
        if st.button("Sauvegarder les Modifications"):
            output_file_path = "updated_keywords_category.csv"
            edited_df.to_csv(uploaded_file, index=False, encoding='utf-8-sig')
            st.success("Modifications sauvegardées avec succès !")

    # Subsection 3: telechargement pdfs pour une muni
    with st.expander("Voulez-vous analyser les documents pour une municipalité?"):
        excel_path = 'MUN.csv'
        df = pd.read_csv(excel_path)

        dfKey = pd.read_csv('keywords_category.csv', encoding='utf-8-sig')
        dfKey['Keywords'] = dfKey['Keywords'].fillna('').astype(str)
        dfKey['Category'] = dfKey['Category'].fillna('').astype(str)
        # Convert the DataFrame to a dictionary
        keywords_dict = {row['Category']: row['Keywords'].split('; ') for _, row in dfKey.iterrows()}

        unique_municipalities = df['munnom'].unique()
        selected_municipality = st.selectbox("Choisissez une municipalité", unique_municipalities, key="unique_municipality_select")

        # Perform analysis based on selection
        if st.button("Analyser"):
            st.write(f"Début du analyse pour {selected_municipality}...")
            print(f"Start analysis for {selected_municipality}")
            munnom_directory = f'pdfs_downloaded_filter/{selected_municipality}' 
            start_time = time.time()  
            process_pdfs_in_folder(munnom_directory, keywords_dict)
            end_time = time.time()  
            time_taken = end_time - start_time 
            print(f"Time taken for {selected_municipality} : {time_taken} seconds") 
            st.write(f"Analyse terminé pour {selected_municipality}!")
            st.write(f"Temps écoulé pour {selected_municipality}: {time_taken} secondes")


    with st.expander("Voulez-vous tout analyser ?"):
        if st.button("Analyser Tout"):
            excel_path = 'MUN.csv'
            df = pd.read_csv(excel_path)

            dfKey = pd.read_csv('keywords_category.csv', encoding='utf-8-sig')
            # Convert the DataFrame to a dictionary
            keywords_dict = {row['Category']: row['Keywords'].split('; ') for _, row in dfKey.iterrows()}

            for index, row in df.iterrows():
                print(f"Start analysis for {row['munnom']}")
                munnom_directory = f'pdfs_downloaded_filter/{row["munnom"]}' 
                start_time = time.time()  
                process_pdfs_in_folder(munnom_directory, keywords_dict)
                end_time = time.time()  
                time_taken = end_time - start_time 
                print(f"Time taken for {row['munnom']} : {time_taken} seconds")  

elif section == "Analyse avancée":
    st.title("Analyse avancée")

    # ---------- Section 1: Texte ----------
    with st.expander("Données quantitatives extraites du texte"):
        try:
            df_keywords = pd.read_excel("ExampleQuantitativesData/Plan_strategique_developpement_durable+keywordsUnites_valuesLLM.xlsx")
            st.dataframe(df_keywords, height=400)
        except Exception as e:
            st.error("❌ Erreur lors du chargement du fichier Excel.")

        # Select and run for a municipality
        try:
            df_loaded = pd.read_csv("MUN.csv")
            unique_municipalities = df_loaded['munnom'].unique()
            selected_muni = st.selectbox("Choisir une municipalité à analyser :", unique_municipalities)

            if st.button("▶️ Lancer l'analyse"):
                folder_path = os.path.join("pdfs_downloaded_filter", selected_muni)
                st.info(f"📁 Dossier analysé : {folder_path}")
                import subprocess
                try:
                    result = subprocess.run(
                    ["python", "advanced_text_extraction.py", folder_path],
                    capture_output=True,
                    text=True,
                    check=True
                )
                    st.success(f"✅ Analyse terminée pour {selected_muni}")
                    st.text_area("🧾 Résultat du script", result.stdout, height=250)
                except subprocess.CalledProcessError as e:
                    st.error("❌ Erreur lors de l'exécution.")
                    st.text_area("🚨 Détails", e.stderr, height=200)

        except Exception as e:
            st.error(f"Erreur chargement municipalités: {e}")


    # ---------- Section 2: Tableaux ----------
    with st.expander("Données quantitatives extraites des tableaux"):
        st.image(r"ExampleQuantitativesData\table.png", caption="Exemple d’extraction à partir d’un tableau", use_column_width=True)




elif section == "MunESGReveal":
    st.title("MunESGReveal")
    st.write("Consultez ou relancez l’analyse ESG pour une municipalité.")

    import matplotlib.pyplot as plt
    import numpy as np

    def plot_category_scores(df):
        grouped = df.groupby('Catégorie')["Score global de la catégorie"].first()
        categories = grouped.index.tolist()
        scores = grouped.values.tolist()

        N = len(categories)
        angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
        width = 2 * np.pi / N

        fig, ax = plt.subplots(figsize=(4, 4), subplot_kw={'polar': True})
        colormap = plt.get_cmap("tab10")
        colors = [colormap(i % 10) for i in range(N)]

        bars = ax.bar(angles, scores, width=width * 0.9, align='edge', edgecolor='black', linewidth=1.5)

        for i, (bar, angle, label, value) in enumerate(zip(bars, angles, categories, scores)):
            bar.set_alpha(0.8)
            bar.set_facecolor(colors[i])
            rotation = np.degrees(angle + width / 2)
            align = 'left' if np.pi/2 < angle < 3*np.pi/2 else 'right'
            ax.text(angle + width / 2, value + 5, f"{label}\n{value}%", ha=align, va='center',
                    rotation=rotation, rotation_mode='anchor', fontsize=5, fontweight='bold')

        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        ax.set_yticklabels([])
        ax.set_xticks([])
        #ax.set_title("Scores par Catégorie", fontsize=14, fontweight='bold', y=1.1)
        st.pyplot(fig)

    base_path = "pdfs_downloaded_filter"
    municipalities = ['Longueuil', 'Saguenay', 'Saint-Jean-sur-Richelieu']
    selected_muni = st.selectbox("Choisissez une municipalité", municipalities)

    # === Show plot from "Scores Agrégés"
    file_path = os.path.join(base_path, selected_muni, 'résultats_complets.xlsx')
    if os.path.exists(file_path):
        df_scores = pd.read_excel(file_path, sheet_name="Scores Agrégés")
        df_scores.columns = df_scores.columns.str.strip()
        plot_category_scores(df_scores)

        # === Then user chooses sheet to display
        sheet_options = ["Scores Agrégés", "Réponses LLM"]
        selected_sheet = st.selectbox("Choisissez les résultats à afficher", sheet_options)

        df = pd.read_excel(file_path, sheet_name=selected_sheet)
        df.columns = df.columns.str.strip()
        

        st.subheader(f"Résultats ESG – {selected_muni} – {selected_sheet}")
        st.dataframe(df, use_container_width=True)

        
    else:
        st.error(f"Fichier introuvable pour {selected_muni}. Veuillez exécuter l’analyse d’abord.")

    # === Option to rerun analysis
    if st.button("▶️ Relancer l’analyse pour cette municipalité"):
        folder = os.path.join("pdfs_downloaded_filter", selected_muni)
        st.info(f"📂 Dossier transmis: {folder}")
        exit_code = os.system(f'python MunESGReveal_V3/main.py "{folder}"')
        if exit_code == 0:
            st.success(f"✅ Analyse relancée pour {selected_muni}.")
        else:
            st.error(f"❌ Échec de l’analyse. Code de sortie: {exit_code}")

