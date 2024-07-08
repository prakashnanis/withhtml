from flask import Flask, request, jsonify, render_template
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
import numpy as np
import os
import faiss  # Import Faiss library

app = Flask(__name__)

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    embeddings_list = []
    for chunk in text_chunks:
        embeddings_list.append(embeddings.encode(chunk))

    # Convert embeddings_list to numpy array
    embeddings_np = np.array(embeddings_list, dtype=np.float32)

    # Initialize Faiss index
    index = faiss.IndexFlatIP(embeddings_np.shape[1])  # IP for inner product similarity

    # Add vectors to Faiss index
    index.add(embeddings_np)

    # Save the index (optional, for later retrieval)
    faiss.write_index(index, "faiss_index.index")

def get_conversational_chain():
    prompt_template = """
    Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
    provided context just say, "answer is not available in the context", don't provide the wrong answer\n\n
    Context:\n {context}?\n
    Question: \n{question}\n

    Answer:
    """

    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain

def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    index = faiss.read_index("faiss_index.index")  # Load Faiss index

    user_embedding = embeddings.encode(user_question)
    user_embedding_np = np.array([user_embedding], dtype=np.float32)

    # Perform similarity search with Faiss
    k = 5  # Number of nearest neighbors to retrieve
    D, I = index.search(user_embedding_np, k)

    docs = []
    for i in I[0]:
        docs.append(text_chunks[i])

    chain = get_conversational_chain()

    response = chain(
        {"input_documents": docs, "question": user_question},
        return_only_outputs=True
    )

    return response["output_text"]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    pdf_docs = request.files.getlist('pdfFile')
    if not pdf_docs:
        return 'No files uploaded', 400

    raw_text = get_pdf_text(pdf_docs)
    text_chunks = get_text_chunks(raw_text)
    get_vector_store(text_chunks)

    return jsonify({'result': 'Files processed successfully'})

@app.route('/ask', methods=['POST'])
def ask_question():
    user_question = request.form.get('question')
    if not user_question:
        return 'No question provided', 400

    answer = user_input(user_question)

    return jsonify({'answer': answer})

if __name__ == '__main__':
    app.run(debug=True)
