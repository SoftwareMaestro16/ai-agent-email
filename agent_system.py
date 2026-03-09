import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader

load_dotenv()

class AgentSystem:
    """
    Agent-based system with tools for course inquiries.
    More flexible than direct RAG - agent decides when to use tools.
    """
    
    def __init__(self, knowledge_file="courses_knowledge.txt"):
        # Load and process knowledge base
        loader = TextLoader(knowledge_file, encoding="utf-8")
        documents = loader.load()
        
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
        
        # Define tool
        @tool
        def search_courses(query: str) -> dict:
            """Search DevCourses knowledge base for course information.
            
            Args:
                query: User's question about courses
                
            Returns:
                Dictionary with context and confidence level
            """
            results = self.vectorstore.similarity_search_with_score(query, k=3)
            
            if not results or results[0][1] > 1.5:
                return {
                    "context": "No relevant information found in knowledge base.",
                    "confidence": "low",
                    "score": 999
                }
            
            context = "\n\n".join([doc.page_content for doc, score in results])
            best_score = results[0][1]
            
            if best_score < 0.8:
                confidence = "high"
            elif best_score < 1.2:
                confidence = "medium"
            else:
                confidence = "low"
            
            return {
                "context": context,
                "confidence": confidence,
                "score": best_score
            }
        
        # Create model
        model = ChatOpenAI(
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.3,
        )
        
        # Create agent with tool
        self.agent = create_agent(
            model=model,
            tools=[search_courses],
            system_prompt="""You are a helpful DevCourses admissions assistant.

RULES:
- For greetings, respond naturally without using tools
- For course questions, ALWAYS use search_courses tool
- ONLY answer based on information from the tool
- If tool returns low confidence, tell user admin will contact them
- NEVER make up information not in the knowledge base
- Be friendly, professional, and encourage enrollment
- Remember conversation context""",
        )
        
        self.conversation_history = []
    
    def answer_question(self, question, user_id="default"):
        """Answer question using agent with tools"""
        config = {"configurable": {"thread_id": user_id}}
        
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": question})
        
        # Invoke agent
        result = self.agent.invoke(
            {"messages": self.conversation_history},
            config=config
        )
        
        # Update history
        if result and "messages" in result:
            self.conversation_history = result["messages"]
            last_msg = self.conversation_history[-1]
            answer = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)
        else:
            answer = str(result)
        
        # Determine confidence from tool usage
        # Check if search_courses was called
        confidence = "medium"  # Default
        
        # Simple heuristic: if answer mentions "admin" or "contact", likely low confidence
        if any(word in answer.lower() for word in ["admin", "contact you", "reach out"]):
            confidence = "low"
        elif len(answer) > 200:  # Detailed answer suggests high confidence
            confidence = "high"
        
        return answer, confidence
    
    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []

if __name__ == "__main__":
    # Test agent system
    agent = AgentSystem()
    
    test_questions = [
        "Hi there!",
        "What courses do you offer?",
        "How much is the Python course?",
        "Do you teach quantum physics?",
    ]
    
    print("🤖 Testing Agent System with Tools\n")
    print("=" * 60)
    
    for q in test_questions:
        print(f"\nQ: {q}")
        answer, confidence = agent.answer_question(q)
        print(f"Confidence: {confidence.upper()}")
        print(f"A: {answer}")
        print("-" * 60)
