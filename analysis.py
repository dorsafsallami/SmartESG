import os
import re
import time
from collections import defaultdict

import pandas as pd
import PyPDF2
from openpyxl.utils.exceptions import IllegalCharacterError
from transformers import (AutoModelForSequenceClassification, AutoTokenizer,
                          pipeline)


# Function to extract phrases with the keyword approximately in the middle from a long context
def extract_keyword_phrase_centered(context, keyword, start_index, span=50):
    # Convert to lowercase for case-insensitive search
    context_lower = context.lower()
    keyword_lower = keyword.lower()

    # Find the index of the keyword in the context starting from 'start_index'
    keyword_index = context_lower.find(keyword_lower, start_index)
    if keyword_index == -1:
        return "Keyword not found in context."

    # Now split the context into words for calculating the span in word terms
    words_before_keyword = context[:keyword_index].split()
    words_after_keyword = context[keyword_index + len(keyword):].split()

    # Calculate how many words are there in the keyword
    keyword_words_count = len(keyword.split())

    # Calculate start and end in terms of words, not characters
    start = max(len(words_before_keyword) - span, 0)
    end = min(len(words_before_keyword) + keyword_words_count + span, len(words_before_keyword) + len(words_after_keyword))

    # Extract words for the final snippet
    final_words = words_before_keyword[start:] + keyword.split() + words_after_keyword[:end - len(words_before_keyword) - keyword_words_count]

    return ' '.join(final_words).strip()


def rename_corrupted_pdf(pdf_path):
    directory, filename = os.path.split(pdf_path)
    new_filename = f"corrupted_{filename}"
    new_pdf_path = os.path.join(directory, new_filename)
    os.rename(pdf_path, new_pdf_path)
    return new_pdf_path

# Function to count occurrences of each keyword and extract context where they appear
def count_keywords_in_pdf(pdf_path, keywords):
    count = defaultdict(lambda: defaultdict(lambda: {'count': 0, 'contexts': []}))

    with open(pdf_path, 'rb') as file:
        try:
            reader = PyPDF2.PdfReader(file)
            for page_number, page in enumerate(reader.pages, start=1):  # Start counting pages from 1
                text = page.extract_text() if page.extract_text() else ''
                text_lower = text.lower()  # Convert text to lower case for case-insensitive search

                for keyword in keywords:
                    keyword_lower = keyword.lower()  # Convert keyword to lower case as well
                    start = 0  # Start position for finding keywords in the text
                    while True:
                        start_index = text_lower.find(keyword_lower, start)  # Find the keyword starting from 'start'
                        if start_index == -1:  # Break the loop if no more keywords are found
                            break
                        # Update count
                        count[keyword_lower][page_number]['count'] += 1
                        # Extract and add context for this keyword occurrence
                        extracted_context = extract_keyword_phrase_centered(text, keyword, start_index)  # You need to modify extract function if it requires start_index
                        count[keyword_lower][page_number]['contexts'].append(extracted_context)
                        start = start_index + len(keyword_lower)  # Move start to just after this occurrence
        except:
            corrupted_pdf_path = rename_corrupted_pdf(pdf_path)
            print(f"Error reading {pdf_file}: EOF marker not found. Renamed to {corrupted_pdf_path}. Skipping this file.")
                    
    return count



# Function to go through all categories
def count_all_categories(pdf_path, lists_dict):
    total_counts = {}
    for category, keywords in lists_dict.items():
        counts = count_keywords_in_pdf(pdf_path, keywords)
        # Convert nested counts into a readable format
        formatted_counts = {}
        for keyword in keywords:  # Change here: iterate through all provided keywords
            keyword_lower = keyword.lower()  # Match the case used in count_keywords_in_pdf
            # If keyword was found in the text
            if keyword_lower in counts:
                pages_detail = {}
                for page, detail in counts[keyword_lower].items():
                    pages_detail[page] = {'count': detail['count'], 'contexts': detail['contexts']}
                formatted_counts[keyword] = {'count': sum(detail['count'] for detail in counts[keyword_lower].values()), 'pages': pages_detail}
            else:  # If no pages found for the keyword
                # Add entry with 'N/A' if keyword not found at all
                formatted_counts[keyword] = {'count': 0, 'pages': {'N/A': {'count': 0, 'contexts': ['N/A']}}}
        
        # Aggregate total counts for each category
        total_counts[category] = formatted_counts
        total_counts[category]['_total'] = sum(formatted_counts[k]['count'] for k in formatted_counts)
    
    return total_counts

def apply_sentiment_analysis(df, text_column):
    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english")
    model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english")
    
    # Create a sentiment analysis pipeline with explicit tokenizer and model
    sentiment_pipeline = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer, truncation=True)
    
    # Function to apply sentiment analysis, now with tokenizer handling truncation
    def analyze_sentiment(text):
        if text == 'N/A':  # Check if context is 'N/A'
            return 'N/A', 'N/A'  # Return 'N/A' for both label and score
        else:
            result = sentiment_pipeline(text)
            # Extract label and score from the result
            label = result[0]['label']
            score = result[0]['score']
            return label, score
    
    # Apply sentiment analysis to each row of the dataframe
    df['sentiment_label'], df['sentiment_score'] = zip(*df[text_column].apply(analyze_sentiment))
    return df



# Function to clean illegal characters from a string
def clean_illegal_characters(text):
    ILLEGAL_CHARACTERS_RE = re.compile(
        r'[\000-\010]|[\013-\014]|[\016-\037]'
    )
    if isinstance(text, str):
        return ILLEGAL_CHARACTERS_RE.sub("", text)
    return text

def text_analysis_context_sentiment(folder_path, pdf_path, keywords_dict):
    start_time = time.time()  # Record the start time

    # Get the counts for all categories
    all_counts = count_all_categories(pdf_path, keywords_dict)
    
    # Prepare data for DataFrame with context adjustment
    data = []
    for category, counts in all_counts.items():
        for keyword, details in counts.items():
            if keyword != '_total':  # Skip the total count
                for page_num, detail in details['pages'].items():
                    for context in detail['contexts']:
                        data.append({
                            'Category': category,
                            'Keyword': keyword,
                            'Count': details['count'],
                            'Page Number': page_num,
                            'Context': context
                        })
    df = pd.DataFrame(data)
    
    # Apply sentiment analysis to each row of the dataframe
    df = apply_sentiment_analysis(df, 'Context')
    
    # Saving the DataFrame to an Excel file
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    excel_path = os.path.join(folder_path, f'{base_name}.xlsx')
    
    try:
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        print(f'Results saved to {excel_path}')
    except IllegalCharacterError:
        # Clean DataFrame
        df = df.applymap(clean_illegal_characters)
        # Retry saving the DataFrame to an Excel file
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        print(f'Results saved to {excel_path} after cleaning illegal characters')

    end_time = time.time()  # Record the end time
    execution_time = end_time - start_time  # Calculate the execution time
    print(f'Execution time: {execution_time} seconds')  # Print the execution time

# Function to save information to a text file in the specified folder
def save_info(message, folder_path, filename="alert.txt"):
    file_path = os.path.join(folder_path, filename)
    # Ensure the folder exists
    os.makedirs(folder_path, exist_ok=True)
    # Append to the file, creating it if it doesn't exist
    with open(file_path, "a", encoding='utf-8') as file:
        file.write(message + "\n")

# Function to show a pop-up alert
def show_alert(message, folder_path):
    save_info(message, folder_path)
    
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
    
    # Close the pop-up automatically after 1 second
    top.after(1000, top.destroy)  # 1000 milliseconds = 1 second
    
    # Run the main loop for a short period to ensure the window appears
    root.after(1100, root.quit)
    root.mainloop()
# Function to process PDFs in a folder
def process_pdfs_in_folder(folder_path, keywords_dict):
    # List all PDF files in the directory
    pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]
    # Check if the folder exists, if not, create it
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        
    # Start timing
    start_time = time.time()
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(folder_path, pdf_file)
        
        # Construct the base name and Excel path
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        excel_path = os.path.join(folder_path, f'{base_name}.xlsx')
        
        # Check if the Excel file exists
        if os.path.exists(excel_path):
            message = f"The file {excel_path} already exists."
            show_alert(message, folder_path)
            continue  
        
       
        
        try:
            text_analysis_context_sentiment(folder_path, pdf_path, keywords_dict)
        except:
            print("EOF marker not found in the PDF file.")
            corrupted_pdf_path = rename_corrupted_pdf(pdf_path)
            print(f"Error reading {pdf_file}: EOF marker not found. Renamed to {corrupted_pdf_path}. Skipping this file.")
            continue        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        print(f"Processed {pdf_file} in {elapsed_time:.2f} seconds")

