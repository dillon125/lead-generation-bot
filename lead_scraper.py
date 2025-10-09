import os
import requests
import pandas as pd
from datetime import datetime
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

class LeadGenerator:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/place"
    
    def search_businesses(self, query, location):
        """Search for businesses using Google Places API"""
        url = f"{self.base_url}/textsearch/json"
        params = {
            'query': f'{query} in {location}',
            'key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json().get('results', [])
        except Exception as e:
            print(f"Error searching {query} in {location}: {e}")
            return []
    
    def get_place_details(self, place_id):
        """Get detailed information about a place"""
        url = f"{self.base_url}/details/json"
        params = {
            'place_id': place_id,
            'fields': 'name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,opening_hours,types',
            'key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json().get('result', {})
        except Exception as e:
            print(f"Error getting details for {place_id}: {e}")
            return {}
    
    def generate_leads(self, queries, locations):
        """Generate leads from multiple queries and locations"""
        all_leads = []
        
        for location in locations:
            for query in queries:
                print(f"Searching: {query} in {location}")
                results = self.search_businesses(query, location)
                
                for result in results:
                    place_id = result.get('place_id')
                    details = self.get_place_details(place_id)
                    
                    # Only include businesses WITHOUT websites
                    if 'website' not in details or not details.get('website'):
                        lead = {
                            'Business Name': result.get('name', 'N/A'),
                            'Address': result.get('formatted_address', 'N/A'),
                            'Phone': details.get('formatted_phone_number', 'N/A'),
                            'Rating': result.get('rating', 'N/A'),
                            'Total Ratings': result.get('user_ratings_total', 0),
                            'Types': ', '.join(result.get('types', [])),
                            'Location Searched': location,
                            'Query Used': query,
                            'Has Website': 'No',
                            'Place ID': place_id
                        }
                        all_leads.append(lead)
                        print(f"  ✓ Found: {lead['Business Name']} (No website)")
                
                time.sleep(1)  # Rate limiting
        
        return all_leads
    
    def save_to_excel(self, leads, filename=None):
        """Save leads to Excel file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'leads_{timestamp}.xlsx'
        
        df = pd.DataFrame(leads)
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"\n✓ Saved {len(leads)} leads to {filename}")
        return filename
    
    def send_email(self, filename, recipient_email, sender_email, sender_password):
        """Send the Excel file via email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = f'New Leads Report - {datetime.now().strftime("%Y-%m-%d")}'
            
            body = f"""
            New leads have been generated!
            
            Total leads found: {len(pd.read_excel(filename))}
            Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            
            See attached Excel file for details.
            
            - Sphere Premier Solutions Lead Bot
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach Excel file
            with open(filename, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={filename}')
                msg.attach(part)
            
            # Send email
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()
            
            print(f"✓ Email sent to {recipient_email}")
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False


def main():
    # Get API key from environment variable
    API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
    
    if not API_KEY:
        print("ERROR: GOOGLE_MAPS_API_KEY environment variable not set!")
        return
    
    # Initialize lead generator
    generator = LeadGenerator(API_KEY)
    
    # Define search parameters queries = [ 'barber shop', 'hair salon', 'dental office', 'dentist', 'real estate agent', 'insurance agent', 'tax preparation', 'accounting services', 'cleaning service', 'landscaping service', 'plumber', 'electrician', 'hvac contractor', 'roofing contractor', 'auto repair shop', 'beauty salon', 'nail salon', 'pet grooming', 'fitness trainer', 'yoga studio' ] locations = [ 'Orlando FL', 'Winter Park FL', 'Kissimmee FL', 'Lake Nona FL', 'Altamonte Springs FL' ]

    
    print("Starting lead generation...")
    print(f"Searching {len(queries)} business types across {len(locations)} locations\n")
    
    # Generate leads
    leads = generator.generate_leads(queries, locations)
    
    if leads:
        # Save to Excel
        filename = generator.save_to_excel(leads)
        
        # Optional: Send email (uncomment and configure if needed)
        # sender_email = os.environ.get('EMAIL_ADDRESS')
        # sender_password = os.environ.get('EMAIL_PASSWORD')
        # recipient_email = 'your-email@example.com'
        # 
        # if sender_email and sender_password:
        #     generator.send_email(filename, recipient_email, sender_email, sender_password)
        
        print(f"\n✅ COMPLETE: Found {len(leads)} businesses without websites!")
    else:
        print("No leads found.")


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
