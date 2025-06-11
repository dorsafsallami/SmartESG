import io
import os
import re
import shutil
import time
import tkinter as tk
import urllib.parse  # For decoding URLs
import zipfile
from collections import Counter, defaultdict

import pandas as pd
import requests
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_pages, extract_text
from pdfminer.layout import LTChar, LTFigure, LTRect, LTTextContainer
from PIL import Image
from transformers import (AutoModelForSequenceClassification, AutoTokenizer,
                          pipeline)


def show_alert(message):
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    top = tk.Toplevel(root)
    top.title("Alert")
    
    # Set the dimensions of the pop-up window
    width = 300
    height = 100
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width / 2) - (width / 2)
    y = (screen_height / 2) - (height / 2)
    top.geometry(f"{width}x{height}+{int(x)}+{int(y)}")
    
    # Display the message
    message_label = tk.Label(top, text=message)
    message_label.pack(expand=True)
    
    # Add a Decline button
    def decline():
        top.destroy()

    decline_button = tk.Button(top, text="Decline", command=decline)
    decline_button.pack(side=tk.BOTTOM, pady=10)
    
    root.update()


def extract_publication_date(pdf_path):
    try:
        # Open the PDF file
        pdf_document = fitz.open(pdf_path)

        # Get the first page
        first_page = pdf_document[0]

        # Extract text from the first page
        text = first_page.get_text()

        # Attempt to find any year
        year_pattern = r'\b(19\d{2}|20\d{2})\b'
        matches = re.findall(year_pattern, text)
        
        if matches:
            publication_year = matches[0]
            return publication_year
        else:
            return "No_date"
    except Exception as e:
        return "No_date"

def contains_keywords(pdf_name, keywords):
    """
    Check if the PDF name contains any of the specified keywords and a year within the given range.
    
    :param pdf_name: Name of the PDF file.
    :param keywords: List of keywords to check in the PDF name.
    :return: True if conditions are met, False otherwise.
    """
    # Convert the PDF name to lowercase and replace separators with spaces
    modified_pdf_name = pdf_name.lower().replace('_', ' ').replace('-', ' ').replace('.', ' ')
   
    # Check if any keyword is in the modified PDF name
    for keyword in keywords:
        if keyword.lower() in modified_pdf_name:
            return True  # A keyword is found in the PDF name
    
    return False  # No keywords found

def create_directory(directory_path):
    """
    Creates a directory if it doesn't already exist.
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

def download_pdfs_from_url(munnom, url, munnom_directory, visited_urls, downloaded_pdfs, skipped_files_info, keywords, depth=0, max_depth=10):
    
    if url in visited_urls or depth > max_depth:
        return
    visited_urls.add(url)

    try:
        # Get the HTML of the page
        response = requests.get(url)
        response.raise_for_status()  # Ensure the request was successful
        html = response.text
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve {url}: {e}")
        return  # Skip this URL if there are any issues retrieving it

    # Switch to a more lenient parser to handle malformed HTML better
    soup = BeautifulSoup(html, 'lxml')  # Corrected 'html.parser' to 'lxml'

    # Find all hyperlinks present on the webpage
    links = soup.find_all('a')
    for link in links:
        href = link.get('href')
        if href:
            # Complete the URL if it's relative
            full_url = href if href.startswith('http') else urllib.parse.urljoin(url, href)

            # Check if the link is to a PDF and download it
            if '.pdf' in href:
                # Decode the URL to get a proper file name
                decoded_url = urllib.parse.unquote(full_url)
                pdf_name = decoded_url.split('/')[-1].replace(' ', '_')  # Replace spaces with underscores
                
                # Sanitize the pdf_name to remove or replace characters not allowed in file names
                invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
                for char in invalid_chars:
                    pdf_name = pdf_name.replace(char, '_')
                    


                # Check if the PDF has already been downloaded
                if (pdf_name not in downloaded_pdfs) and (contains_keywords(pdf_name, keywords)):
                    try:
                        pdf_response = requests.get(full_url)
                        pdf_response.raise_for_status()  # Check if the request was successful
                        pdf_content = pdf_response.content
                        
                        # Save the PDF to disk
                        pdf_path = os.path.join(munnom_directory, pdf_name)
                        with open(pdf_path, 'wb') as f:
                            f.write(pdf_content)
                        
                        # Add the downloaded PDF to the set
                        downloaded_pdfs.add(pdf_name)
                        print(f"File downloaded: {pdf_name}")
                        try:
                            publication_year = extract_publication_date(pdf_path)
                            # Generate new name
                            new_name = f"{publication_year}_{pdf_name}"
                            new_path = os.path.join(munnom_directory, new_name)

                            # Rename the file
                            try:
                                shutil.move(pdf_path, new_path)
                                print(f"Renamed '{pdf_name}' to '{new_name}'")
                            except FileNotFoundError as e:
                                print(f"Error renaming '{pdf_name}': {e}")

                        except Exception as e:
                            print(f"Error processing '{pdf_name}': {e}")
                            
                    except requests.exceptions.RequestException as e:
                        print(f"Failed to download {full_url}: {e}")
                
                    
                if pdf_name not in downloaded_pdfs:
                        skipped_files_info.append({
                            'mumu': munnom,
                             'file_name': pdf_name,
                              'file_link': full_url
                         })
                        print(f"File skipped (keyword filter): {pdf_name}")

            # If the link is not a PDF and is a page within the same site, recurse into it with increased depth
            elif urllib.parse.urlparse(full_url).netloc == urllib.parse.urlparse(url).netloc:
                download_pdfs_from_url(munnom, full_url, munnom_directory, visited_urls, downloaded_pdfs, skipped_files_info, keywords, depth + 1, max_depth)

    print(f"All available PDF files from {url} have been downloaded.")


