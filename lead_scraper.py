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
            'fields': 'name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,opening_hours,types,business_status',
            'key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json().get('result', {})
        except Exception as e:
            print(f"Error getting details for {place_id}: {e}")
            return {}
    
    def extract_email_from_text(self, text):
        """Extract email from text using basic pattern matching"""
        import re
        if not text:
            return None
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else None
    
    def generate_leads(self, queries, locations):
        """Generate leads from multiple queries and locations"""
        all_leads = []
        seen_places = set()
        
        for location in locations:
            for query in queries:
                print(f"Searching: {query} in {location}")
                results = self.search_businesses(query, location)
                
                for result in results:
                    place_id = result.get('place_id')
                    
                    # Skip duplicates
                    if place_id in seen_places:
                        continue
                    seen_places.add(place_id)
                    
                    details = self.get_place_details(place_id)
                    
                    # Only include businesses WITHOUT websites
                    if 'website' not in details or not details.get('website'):
                        # Try to extract email from name or address (limited success)
                        email = self.extract_email_from_text(result.get('name', ''))
                        if not email:
                            email = self.extract_email_from_text(result.get('formatted_address', ''))
                        
                        lead = {
                            'Business Name': result.get('name', 'N/A'),
                            'Address': result.get('formatted_address', 'N/A'),
                            'Phone': details.get('formatted_phone_number', 'N/A'),
                            'Email': email if email else 'Not Found',
                            'Rating': result.get('rating', 'N/A'),
                            'Total Ratings': result.get('user_ratings_total', 0),
                            'Business Status': details.get('business_status', 'N/A'),
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
            msg['Subject'] = f'New Leads Report - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
            
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


def run_lead_generation():
    """Main function to run lead generation"""
    print(f"\n{'='*60}")
    print(f"🚀 Starting Lead Generation Run - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Get API key from environment variable
    API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
    
    if not API_KEY:
        print("ERROR: GOOGLE_MAPS_API_KEY environment variable not set!")
        return
    
    # Initialize lead generator
    generator = LeadGenerator(API_KEY)
    
    # Expanded queries with high-value business types
    queries = [
        # Home & Property Services
        'barber shop', 'hair salon', 'beauty salon', 'nail salon', 'spa', 
        'plumber', 'electrician', 'hvac contractor', 'air conditioning service',
        'roofing contractor', 'landscaping service', 'lawn care', 'tree service',
        'pest control', 'pool cleaning', 'fencing contractor', 'paver installer',
        'garage door repair', 'flooring contractor', 'epoxy flooring', 
        'home remodeling', 'handyman service', 'painting contractor', 
        'pressure washing', 'window cleaning', 'solar panel installer',
        'gutter cleaning', 'water damage restoration', 'junk removal', 
        'appliance repair', 'locksmith', 'home cleaning service',
        'interior designer', 'real estate agent', 'property management',
        'mortgage broker', 'home inspector', 'contractor supply store',
        
        # Auto & Transport
        'auto repair shop', 'auto detailing', 'car wash', 'tire shop',
        'tow truck service', 'auto glass repair', 'transmission shop',
        'car dealership', 'body shop', 'mobile mechanic', 'window tinting',
        
        # Health & Wellness
        'dental office', 'dentist', 'chiropractor', 'physical therapy',
        'massage therapy', 'yoga studio', 'fitness center', 'personal trainer',
        'medical spa', 'weight loss clinic', 'acupuncture',
        
        # Professional Services
        'insurance agent', 'tax preparation', 'accounting services',
        'financial advisor', 'lawyer', 'attorney', 'notary public',
        'business consulting', 'marketing agency', 'printing service',
        
        # Retail & Food
        'pet grooming', 'pet store', 'bakery', 'cafe', 'restaurant',
        'catering service', 'food truck', 'grocery store', 'liquor store',
        'convenience store', 'clothing boutique', 'jewelry store'
    ]
    
    # Expanded Florida locations (covers Central FL thoroughly)
    locations = [
        # Greater Orlando Area
        'Orlando FL', 'Winter Park FL', 'Kissimmee FL', 'Lake Nona FL', 
        'Altamonte Springs FL', 'Sanford FL', 'Oviedo FL', 'Winter Garden FL',
        'Maitland FL', 'Apopka FL', 'Clermont FL', 'Windermere FL',
        'Lake Mary FL', 'Longwood FL', 'Casselberry FL', 'Winter Springs FL',
        
        # Surrounding Cities
        'Davenport FL', 'Haines City FL', 'Poinciana FL', 'Celebration FL',
        'St Cloud FL', 'Deltona FL', 'DeLand FL', 'Mount Dora FL',
        'Leesburg FL', 'Eustis FL', 'The Villages FL',
        
        # Other Major FL Markets
        'Tampa FL', 'St Petersburg FL', 'Clearwater FL', 'Lakeland FL',
        'Melbourne FL', 'Cocoa Beach FL', 'Palm Bay FL', 'Vero Beach FL',
        'Ocala FL', 'Gainesville FL', 'Daytona Beach FL', 'Port Orange FL'
    ]
    
    print(f"Searching {len(queries)} business types across {len(locations)} locations\n")
    
    # Generate leads
    leads = generator.generate_leads(queries, locations)
    
    if leads:
        # Save to Excel
        filename = generator.save_to_excel(leads)
        
        # Optional: Send email (configure environment variables to enable)
        sender_email = os.environ.get('EMAIL_ADDRESS')
        sender_password = os.environ.get('EMAIL_PASSWORD')
        recipient_email = os.environ.get('RECIPIENT_EMAIL', 'your-email@example.com')
        
        if sender_email and sender_password:
            generator.send_email(filename, recipient_email, sender_email, sender_password)
        else:
            print("\n⚠️  Email not configured. Set EMAIL_ADDRESS and EMAIL_PASSWORD to enable auto-emailing.")
        
        print(f"\n✅ COMPLETE: Found {len(leads)} businesses without websites!")
    else:
        print("No leads found.")
    
    print(f"\n{'='*60}")
    print(f"✅ Lead Generation Complete - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")


def main():
    """Run lead generation once"""
    run_lead_generation()


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
