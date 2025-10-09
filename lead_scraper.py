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
            'query': f"{query} in {location}",
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
            'fields': 'name,formatted_address,formatted_phone_number,website,rating,user_ratings_total',
            'key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json().get('result', {})
        except Exception as e:
            print(f"Error getting details for {place_id}: {e}")
            return {}
    
    def generate_leads(self, city, industries, max_per_industry=20):
        """Generate leads for businesses without websites"""
        all_leads = []
        
        print(f"\n🔍 Searching {city}...")
        
        for industry in industries:
            print(f"  📋 {industry}...")
            businesses = self.search_businesses(industry, city)
            
            for biz in businesses[:max_per_industry]:
                time.sleep(0.5)  # Rate limiting
                
                details = self.get_place_details(biz.get('place_id'))
                
                # Only add if NO website
                if not details.get('website'):
                    lead = {
                        'Business Name': details.get('name', 'N/A'),
                        'Phone': details.get('formatted_phone_number', 'N/A'),
                        'Address': details.get('formatted_address', 'N/A'),
                        'City': city,
                        'Industry': industry,
                        'Rating': details.get('rating', 'N/A'),
                        'Reviews': details.get('user_ratings_total', 'N/A'),
                        'Email Template': f"Hi! I noticed {details.get('name')} doesn't have a website. I help {industry} businesses get online. 15 min call?"
                    }
                    all_leads.append(lead)
                    print(f"    ✅ {lead['Business Name']}")
        
        return all_leads
    
    def save_to_excel(self, leads, filename):
        """Save leads to Excel file"""
        if not leads:
            print("⚠️  No leads found (all had websites)")
            return None
        
        df = pd.DataFrame(leads)
        df.to_excel(filename, index=False)
        print(f"\n✅ Saved {len(leads)} leads to {filename}")
        return filename
    
    def send_email(self, filename, recipient):
        """Send Excel file via email"""
        try:
            sender = os.environ.get('GMAIL_USER')
            password = os.environ.get('GMAIL_APP_PASSWORD')
            
            if not sender or not password:
                print("⚠️  Email credentials not configured")
                return
            
            msg = MIMEMultipart()
            msg['From'] = sender
            msg['To'] = recipient
            msg['Subject'] = f"🎯 New Leads - {datetime.now().strftime('%B %d, %Y %I:%M %p')}"
            
            body = f"""
            New leads scraped and ready!
            
            File attached: {filename}
            
            Import directly into GoHighLevel and start calling! 📞
            
            - Lead Generation Bot 🤖
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach Excel file
            with open(filename, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={filename}')
                msg.attach(part)
            
            # Send email
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
            server.quit()
            
            print(f"📧 Email sent to {recipient}")
            
        except Exception as e:
            print(f"❌ Email error: {e}")


def main():
    # Configuration
    API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
    EMAIL = 'Michael@spherepremier.com'
    
    # Top 50 US Cities (rotates every 3 hours)
    CITIES = [
        'Los Angeles, CA', 'New York, NY', 'Chicago, IL', 'Houston, TX',
        'Phoenix, AZ', 'Philadelphia, PA', 'San Antonio, TX', 'San Diego, CA',
        'Dallas, TX', 'Austin, TX', 'Jacksonville, FL', 'Fort Worth, TX',
        'San Jose, CA', 'Charlotte, NC', 'Columbus, OH', 'Indianapolis, IN',
        'San Francisco, CA', 'Seattle, WA', 'Denver, CO', 'Boston, MA',
        'Nashville, TN', 'Detroit, MI', 'Portland, OR', 'Las Vegas, NV',
        'Memphis, TN', 'Louisville, KY', 'Baltimore, MD', 'Milwaukee, WI',
        'Albuquerque, NM', 'Tucson, AZ', 'Fresno, CA', 'Sacramento, CA',
        'Mesa, AZ', 'Kansas City, MO', 'Atlanta, GA', 'Miami, FL',
        'Raleigh, NC', 'Omaha, NE', 'Colorado Springs, CO', 'Virginia Beach, VA',
        'Oakland, CA', 'Minneapolis, MN', 'Tulsa, OK', 'Tampa, FL',
        'Arlington, TX', 'New Orleans, LA', 'Wichita, KS', 'Cleveland, OH',
        'Bakersfield, CA', 'Orlando, FL'
    ]
    
    # MAXIMUM industries - 60+ categories
    INDUSTRIES = [
        # Beauty & Personal Care
        'hair salon',
        'barbershop',
        'nail salon',
        'spa',
        'massage therapist',
        'tattoo shop',
        'beauty salon',
        'tanning salon',
        'eyelash extensions',
        'med spa',
        
        # Health & Wellness
        'gym',
        'fitness studio',
        'yoga studio',
        'pilates studio',
        'martial arts school',
        'chiropractor',
        'physical therapy',
        'acupuncture',
        'nutritionist',
        'counseling',
        
        # Home Services
        'plumber',
        'electrician',
        'HVAC company',
        'roofing company',
        'painting contractor',
        'landscaping company',
        'lawn care service',
        'tree service',
        'pest control',
        'cleaning service',
        'carpet cleaning',
        'window cleaning',
        'handyman service',
        'locksmith',
        'garage door repair',
        
        # Automotive
        'auto repair shop',
        'auto body shop',
        'tire shop',
        'car wash',
        'oil change service',
        'towing service',
        'auto detailing',
        
        # Food & Beverage
        'restaurant',
        'cafe',
        'bakery',
        'juice bar',
        'catering service',
        
        # Pet Services
        'pet groomer',
        'dog trainer',
        'veterinarian',
        'pet boarding',
        
        # Professional Services
        'accounting firm',
        'tax preparation',
        'insurance agency',
        'real estate agent',
        'photography studio',
        'event planner'
    ]
    
    # Determine which city based on time (rotates every 3 hours)
    hour = datetime.now().hour
    city_index = (hour // 3) % len(CITIES)
    current_city = CITIES[city_index]
    
    print(f"🚀 Lead Generation Bot Starting...")
    print(f"📍 Target City: {current_city}")
    print(f"⏰ Time: {datetime.now().strftime('%I:%M %p')}")
    print(f"🎯 Industries: {len(INDUSTRIES)} categories")
    
    # Generate leads
    generator = LeadGenerator(API_KEY)
    leads = generator.generate_leads(current_city, INDUSTRIES, max_per_industry=20)
    
    # Save and email
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    filename = f"leads_{current_city.replace(', ', '_').replace(' ', '_')}_{timestamp}.xlsx"
    
    if generator.save_to_excel(leads, filename):
        generator.send_email(filename, EMAIL)
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
