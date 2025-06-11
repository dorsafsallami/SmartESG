# llm_agent.py
import faiss
import numpy as np
import openai
from sklearn.metrics.pairwise import cosine_similarity


def split_document(doc, max_chars=3000, overlap=200):
    """
    Splits a long document into smaller chunks.
    
    :param doc: The full document string.
    :param max_chars: Maximum number of characters per chunk.
    :param overlap: Number of overlapping characters between chunks.
    :return: A list of document chunks.
    """
    chunks = []
    start = 0
    while start < len(doc):
        end = start + max_chars
        chunks.append(doc[start:end])
        start += max_chars - overlap
    return chunks

class LLMAgent:
    """
    Implements a Retrieval-Augmented Generation (RAG) pipeline using FAISS and OpenAI embeddings.
    """
    def __init__(self):
        self.documents = []
        self.embeddings = []
        self.index = None

    def build_knowledge_base(self, list_of_texts):
        """
        Builds a FAISS index from a list of text documents. 
        If a document is too long, it will be split into smaller chunks.
        
        :param list_of_texts: List of strings (each could be a PDF+Excel combined text)
        """
        self.documents = []
        self.embeddings = []
        for doc in list_of_texts:
            # If the document is too long, split it
            if len(doc) > 3000:
                chunks = split_document(doc, max_chars=3000, overlap=200)
                self.documents.extend(chunks)
            else:
                self.documents.append(doc)

        if not self.documents:
            print("Aucun document à indexer.")
            return

        for doc in self.documents:
            resp = openai.Embedding.create(input=doc, model="text-embedding-ada-002")
            embedding = resp['data'][0]['embedding']
            self.embeddings.append(np.array(embedding, dtype=np.float32))

        embedding_dim = len(self.embeddings[0])
        self.index = faiss.IndexFlatL2(embedding_dim)
        self.index.add(np.stack(self.embeddings))

    """def retrieve_relevant_chunks(self, query, top_k=5):
        
        Retrieves the most relevant chunks from the knowledge base for a given query.
        
        if not self.index or not self.embeddings:
            return []
        resp = openai.Embedding.create(input=query, model="text-embedding-ada-002")
        query_vec = np.array(resp['data'][0]['embedding'], dtype=np.float32).reshape(1, -1)
        distances, indices = self.index.search(query_vec, top_k)
        return [self.documents[idx] for idx in indices[0]]"""

    def retrieve_relevant_chunks(self, query, top_k=5, rerank_top_k=3):
        if not self.index or not self.embeddings:
            return []

        # Embedding de la requête
        resp = openai.Embedding.create(input=query, model="text-embedding-ada-002")
        query_vec = np.array(resp['data'][0]['embedding'], dtype=np.float32).reshape(1, -1)

        # Recherche initiale avec FAISS
        distances, indices = self.index.search(query_vec, top_k)

        # Récupération des documents et embeddings correspondants
        retrieved_docs = [self.documents[i] for i in indices[0]]
        retrieved_embeds = [self.embeddings[i] for i in indices[0]]

        # Reranking par similarité cosinus
        sims = cosine_similarity(query_vec, np.stack(retrieved_embeds))[0]  # shape: (top_k,)
        ranked_pairs = sorted(zip(sims, retrieved_docs), reverse=True)

        # Retourne les rerank_top_k documents les plus pertinents
        return [doc for _, doc in ranked_pairs[:rerank_top_k]]

    def answer_query(self, query):
        """
        Retrieves relevant documents from the knowledge base and queries the LLM with that context.
        Returns the LLM's answer.
        """
        top_docs = self.retrieve_relevant_chunks(query, top_k=5)
        context = "\n".join(top_docs)
        #system_prompt = (
            #"Vous êtes un assistant AI spécialisé dans l'extraction d'informations à partir de rapports municipaux "
           # "et de données Excel. Répondez de manière concise en vous basant uniquement sur le contexte fourni."
        #)

        system_prompt = (
                 "Vous êtes un assistant AI spécialisé dans l'analyse de rapports municipaux. "
                 "Votre rôle est non seulement de répondre aux questions, mais aussi de justifier clairement vos réponses à partir du contexte fourni."
        ) 

        #user_prompt = (
         #   f"Contexte:\n{context}\n\n"
         #   f"Question: {query}\n"
          #  "Répondez de manière concise en français."
        #)


       # user_prompt = (
        #   f"Contexte:\n{context}\n\n"
         #  f"Question: {query}\n"
           #"Répondez de manière détaillée en français. "
           #"Expliquez pourquoi vous donnez cette réponse, en vous basant explicitement sur des éléments du contexte fourni. "
           #"Mentionnez les phrases clés ou données spécifiques qui justifient votre analyse."
        #)

        user_prompt = (
                  f"Contexte:\n{context}\n\n"
                  f"Question: {query}\n"
                  "Consignes pour votre réponse :\n"
                  "1. Votre réponse doit être précise, complète et strictement fondée sur les informations textuelles fournies.\n"
                  "2. N’utilisez pas de langage d’embellissement. Gardez votre réponse aussi proche que possible des données originales.\n"
                  "3. Si une entité est mentionnée dans la question, assurez-vous de la mentionner également dans votre réponse.\n"
                  "4. N’utilisez que les informations nécessaires à la formulation d’une réponse détaillée.\n"
                  "5. Si vous n’êtes pas sûr, reconnaissez simplement le manque d’information au lieu d’inventer une réponse.\n"
                )

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0
        )
        return response['choices'][0]['message']['content']
