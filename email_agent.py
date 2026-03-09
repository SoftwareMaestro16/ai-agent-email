import os
import time
from datetime import datetime
from dotenv import load_dotenv
from rag_system import RAGSystem

load_dotenv()

class SimpleEmailAgent:
    """
    Simplified email agent that simulates email processing.
    For production, integrate with actual email service (SendGrid, Mailgun, etc.)
    """
    
    def __init__(self):
        self.admin_email = "softwaremaestro16@gmail.com"
        self.rag = RAGSystem()
        self.processed_questions = []
        
    def notify_admin(self, user_email, question, reason="uncertain"):
        """Simulate admin notification"""
        notification = f"""
{'='*60}
ADMIN NOTIFICATION
{'='*60}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
From: {user_email}
Reason: {reason}

Question:
{question}

Action Required: Manual review and response needed
{'='*60}
"""
        print(notification)
        
        # In production, send actual email to admin
        # Example: send_email(self.admin_email, subject, body)
        
        return True
    
    def process_question(self, question, user_email):
        """Process question with RAG and determine confidence"""
        print(f"\n📧 Processing question from: {user_email}")
        print(f"Question: {question}\n")
        
        response, confidence = self.rag.answer_question(question)
        
        print(f"🎯 Confidence: {confidence.upper()}")
        
        # If low confidence, notify admin
        if confidence == "low":
            print("⚠️  Low confidence - Notifying admin...")
            self.notify_admin(user_email, question, "Low confidence in answer")
            
            final_response = f"""Thank you for your question about DevCourses!

{response}

For more detailed information, our admissions team will contact you shortly at {user_email}.

Best regards,
DevCourses Team
Website: www.devcourses.com
Email: admissions@devcourses.com"""
        else:
            final_response = f"""Thank you for your question about DevCourses!

{response}

If you have more questions, feel free to contact us at admissions@devcourses.com.

Best regards,
DevCourses Team
Email: admissions@devcourses.com
Phone: +1 (555) 123-4567"""
        
        print("\n📤 Response to user:")
        print("-" * 60)
        print(final_response)
        print("-" * 60)
        
        self.processed_questions.append({
            'user': user_email,
            'question': question,
            'confidence': confidence,
            'timestamp': datetime.now()
        })
        
        return final_response
    
    def simulate_email_flow(self):
        """Simulate email questions for testing"""
        test_emails = [
            {
                'from': 'student1@example.com',
                'question': 'What courses do you offer in backend development?'
            },
            {
                'from': 'student2@example.com', 
                'question': 'How much does the Python course cost?'
            },
            {
                'from': 'student3@example.com',
                'question': 'Do you teach quantum physics?'
            },
            {
                'from': 'student4@example.com',
                'question': 'When is the next React course starting?'
            }
        ]
        
        print("🤖 DevCourses Email Agent - Simulation Mode")
        print("=" * 60)
        print("Simulating email processing...\n")
        
        for email_data in test_emails:
            self.process_question(email_data['question'], email_data['from'])
            print("\n" + "="*60 + "\n")
            time.sleep(2)
        
        # Summary
        print("\n📊 SUMMARY")
        print("=" * 60)
        print(f"Total questions processed: {len(self.processed_questions)}")
        
        confidence_counts = {}
        for q in self.processed_questions:
            conf = q['confidence']
            confidence_counts[conf] = confidence_counts.get(conf, 0) + 1
        
        for conf, count in confidence_counts.items():
            print(f"{conf.upper()}: {count}")
        
        print("=" * 60)
    
    def interactive_mode(self):
        """Interactive CLI mode for testing"""
        print("🤖 DevCourses Email Agent - Interactive Mode")
        print("=" * 60)
        print("Type questions to test the RAG system")
        print("Commands: 'quit' to exit, 'stats' for statistics\n")
        
        while True:
            user_email = input("User email (or press Enter for test@example.com): ").strip()
            if not user_email:
                user_email = "test@example.com"
            
            question = input("Question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if question.lower() == 'stats':
                print(f"\n📊 Processed {len(self.processed_questions)} questions")
                continue
            
            if not question:
                continue
            
            self.process_question(question, user_email)
            print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    import sys
    
    agent = SimpleEmailAgent()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'simulate':
        agent.simulate_email_flow()
    else:
        agent.interactive_mode()
