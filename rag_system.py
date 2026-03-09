import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader

load_dotenv()

class RAGSystem:
    def __init__(self, knowledge_file="courses_knowledge.txt"):
        # Load knowledge base
        loader = TextLoader(knowledge_file, encoding="utf-8")
        documents = loader.load()
        
        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        chunks = text_splitter.split_documents(documents)
        
        # Create embeddings and vector store
        embeddings = OpenAIEmbeddings(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1"
        )
        
        self.vectorstore = FAISS.from_documents(chunks, embeddings)
        
        # Create model
        self.model = ChatOpenAI(
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.4,
        )
    
    def search_knowledge(self, query, k=3):
        """Search knowledge base and return results with scores"""
        results = self.vectorstore.similarity_search_with_score(query, k=k)
        return results
    
    def answer_question(self, question):
        """Answer question and return confidence level"""
        # Search knowledge base
        results = self.search_knowledge(question, k=3)
        
        # Check relevance (lower score = more similar)
        if not results or results[0][1] > 1.5:
            return (
                "I don't have specific information about this in my knowledge base. "
                "Please contact our admissions team at admissions@devcourses.com for detailed information.",
                "low"
            )
        
        # Get context
        context = "\n\n".join([doc.page_content for doc, score in results])
        
        # Determine confidence based on best score
        best_score = results[0][1]
        if best_score < 0.8:
            confidence = "high"
        elif best_score < 1.2:
            confidence = "medium"
        else:
            confidence = "low"
        
        # Generate answer
        prompt = f"""You are a helpful DevCourses admissions assistant.

Based on the following information from our knowledge base, answer the user's question.

Knowledge Base Context:
{context}

User Question: {question}

Instructions:
- Answer based ONLY on the provided context
- Be helpful, friendly, and professional
- If the context doesn't fully answer the question, say so
- Keep response concise and clear
- Encourage enrollment when appropriate

Answer:"""
        
        response = self.model.invoke(prompt)
        answer = response.content
        
        return answer, confidence

if __name__ == "__main__":
    # Test RAG system
    rag = RAGSystem()
    
    test_questions = [
        "What courses do you offer?",
        "How much is the Python course?",
        "What is quantum computing?",  # Should have low confidence
    ]
    
    for q in test_questions:
        print(f"\nQ: {q}")
        answer, confidence = rag.answer_question(q)
        print(f"Confidence: {confidence}")
        print(f"A: {answer}\n")
