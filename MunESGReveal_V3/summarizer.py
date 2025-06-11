# summarizer.py
import openai


def chunk_text(text, chunk_size=2000, overlap=200):
    """
    Découpe le texte en segments de taille 'chunk_size' avec un recouvrement.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def summarize_chunk(chunk, model="gpt-3.5-turbo", max_tokens=300):
    """
    Utilise l'API OpenAI pour résumer un segment de texte.
    """
    system_prompt = (
        "Vous êtes un assistant AI spécialisé dans la synthèse de documents municipaux en français. "
        "Veuillez résumer de manière concise le texte suivant."
    )
    user_prompt = f"Texte à résumer:\n\n{chunk}\n\nRésumé concis:"
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0,
        max_tokens=max_tokens
    )
    return response['choices'][0]['message']['content'].strip()

def summarize_text(full_text, chunk_size=2000, overlap=200, model="gpt-3.5-turbo"):
    """
    Découpe et résume un texte long en combinant les résumés de chaque segment.
    """
    chunks = chunk_text(full_text, chunk_size, overlap)
    summaries = []
    for chunk in chunks:
        summaries.append(summarize_chunk(chunk, model=model))
    return "\n".join(summaries)
