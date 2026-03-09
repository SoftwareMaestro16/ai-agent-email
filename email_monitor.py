import os
import time
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from dotenv import load_dotenv
from agent_system import AgentSystem  # Use agent instead of RAG

load_dotenv()

class EmailMonitor:
    """
    Real email monitoring agent using IMAP/SMTP with AI agent + tools.
    """
    
    def __init__(self):
        self.email_address = os.getenv("EMAIL_ADDRESS")
        self.email_password = os.getenv("EMAIL_APP_PASSWORD")
        self.admin_email = "softwaremaestro16@gmail.com"
        
        # Email server settings
        self.imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com")
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        
        self.agent = AgentSystem()  # Use agent with tools
        self.processed_emails = set()
        self.start_time = datetime.now(timezone.utc)  # Use UTC timezone
        
        print(f"📧 Email: {self.email_address}")
        print(f"🔧 IMAP: {self.imap_server}")
        print(f"🔧 SMTP: {self.smtp_server}:{self.smtp_port}")
        print(f"⏰ Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # Mark all existing unread emails as processed (ignore old emails)
        print(f"\n🧹 Marking all existing unread emails as processed...")
        self.mark_existing_emails_as_processed()
        print(f"✅ Ready to process NEW emails only!\n")
    
    def connect_imap(self):
        """Connect to IMAP server"""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email_address, self.email_password)
            return mail
        except Exception as e:
            print(f"❌ IMAP connection failed: {e}")
            return None
    
    def mark_existing_emails_as_processed(self):
        """Mark all existing unread emails as processed to ignore them"""
        mail = self.connect_imap()
        if not mail:
            return
        
        try:
            mail.select('INBOX')
            status, messages = mail.search(None, 'UNSEEN')
            email_ids = messages[0].split()
            
            print(f"   Found {len(email_ids)} existing unread emails")
            
            for email_id in email_ids:
                self.processed_emails.add(email_id)
            
            print(f"   Marked {len(email_ids)} emails as processed (will ignore)")
            
            mail.close()
            mail.logout()
            
        except Exception as e:
            print(f"   ⚠️ Error: {e}")
    
    def send_email(self, to_email, subject, body):
        """Send email via SMTP"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_address, self.email_password)
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Email sent to {to_email}")
            return True
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
    
    def notify_admin(self, user_email, question):
        """Notify admin about uncertain question"""
        subject = f"[DevCourses] Question Needs Review - {user_email}"
        body = f"""Hello Admin,

A user asked a question that requires manual review.

From: {user_email}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Question:
{question}

Please respond to the user directly.

---
DevCourses AI Agent
"""
        return self.send_email(self.admin_email, subject, body)
    
    def process_question(self, question, user_email):
        """Process question with AI agent + tools"""
        response, confidence = self.agent.answer_question(question, user_id=user_email)
        
        if confidence == "low":
            self.notify_admin(user_email, question)
            return f"""Thank you for contacting DevCourses!

{response}

Our admissions team will contact you shortly with detailed information.

Best regards,
DevCourses Team
Website: www.devcourses.com
Email: admissions@devcourses.com"""
        
        return f"""Thank you for contacting DevCourses!

{response}

If you have more questions, feel free to reply or visit www.devcourses.com.

Best regards,
DevCourses Team
Email: admissions@devcourses.com
Phone: +1 (555) 123-4567"""
    
    def check_emails(self):
        """Check for new unread emails"""
        mail = self.connect_imap()
        if not mail:
            return
        
        try:
            mail.select('INBOX')
            
            # Search for ALL unread emails
            status, messages = mail.search(None, 'UNSEEN')
            email_ids = messages[0].split()
            
            # Filter out already processed emails
            new_email_ids = [eid for eid in email_ids if eid not in self.processed_emails]
            
            if new_email_ids:
                print(f"\n📬 Found {len(new_email_ids)} NEW unread emails!")
            
            for email_id in new_email_ids:
                # Fetch email
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        from_email = email.utils.parseaddr(msg['From'])[1]
                        subject = msg['Subject'] or "(No Subject)"
                        
                        # Get body
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    body = part.get_payload(decode=True).decode()
                                    break
                        else:
                            body = msg.get_payload(decode=True).decode()
                        
                        print(f"\n📨 Processing email from: {from_email}")
                        print(f"   Subject: {subject}")
                        print(f"   Question: {body[:100]}...")
                        
                        # Process and respond
                        print(f"   🤖 Generating response...")
                        response = self.process_question(body, from_email)
                        
                        print(f"   📤 Sending reply...")
                        reply_subject = f"Re: {subject}" if not subject.startswith("Re:") else subject
                        self.send_email(from_email, reply_subject, response)
                        
                        # Mark as processed
                        self.processed_emails.add(email_id)
                        print(f"   ✅ Done!")
            
            mail.close()
            mail.logout()
            
        except Exception as e:
            import traceback
            print(f"❌ Error checking emails: {e}")
            print(traceback.format_exc())
    
    def run(self, interval=60):
        """Run email monitoring loop"""
        print("\n🤖 DevCourses Email Monitor Started")
        print(f"⏱️  Check interval: {interval} seconds")
        print("Press Ctrl+C to stop\n")
        
        while True:
            try:
                self.check_emails()
                time.sleep(interval)
            except KeyboardInterrupt:
                print("\n\n👋 Stopping email monitor...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(interval)

if __name__ == "__main__":
    # Check credentials
    if not os.getenv("EMAIL_ADDRESS") or not os.getenv("EMAIL_APP_PASSWORD"):
        print("❌ Error: EMAIL_ADDRESS and EMAIL_APP_PASSWORD must be set in .env")
        print("\nFor Gmail:")
        print("1. Enable 2FA: https://myaccount.google.com/security")
        print("2. Create App Password: https://myaccount.google.com/apppasswords")
        print("3. Add to .env:")
        print("   EMAIL_ADDRESS=your_email@gmail.com")
        print("   EMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx")
        exit(1)
    
    monitor = EmailMonitor()
    monitor.run(interval=30)  # Check every 30 seconds
