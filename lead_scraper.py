import os
import requests
import pandas as pd
from datetime import datetime
import time

# ========================================
# ENTER YOUR API KEY HERE:
API_KEY = "PASTE_YOUR_API_KEY_HERE"
# ========================================

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
                    
                    if place_id in seen_places:
                        continue
                    seen_places.add(place_id)
                    
                    details = self.get_place_details(place_id)
                    
                    # Only include businesses WITHOUT websites
                    if 'website' not in details or not details.get('website'):
                        lead = {
                            'Business Name': result.get('name', 'N/A'),
                            'Address': result.get('formatted_address', 'N/A'),
                            'Phone': details.get('formatted_phone_number', 'N/A'),
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


def main():
    """Main function to run lead generation"""
    print(f"\n{'='*60}")
    print(f"🚀 Starting Lead Generation - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Check API key
    if API_KEY == "PASTE_YOUR_API_KEY_HERE":
        print("❌ ERROR: Please edit this file and add your Google Maps API Key")
        print("   Open this file in a text editor and replace 'PASTE_YOUR_API_KEY_HERE' with your actual API key")
        input("\nPress Enter to exit...")
        return
    
    # Initialize lead generator
    generator = LeadGenerator(API_KEY)
    
    # Smaller, high-value business types (more likely to not have websites)
    queries = [
        'mobile barber', 'barber shop', 'hair salon', 'beauty salon',
        'lawn care', 'landscaping', 'tree service',
        'handyman', 'junk removal', 'pressure washing',
        'mobile car wash', 'auto detailing',
        'mobile pet grooming', 'pet grooming',
        'house cleaning', 'carpet cleaning'
    ]
    
    # Smaller Florida cities (more likely to have businesses without websites)
    locations = [
        'Apopka FL', 'Sanford FL', 'Ocoee FL', 'Clermont FL',
        'Davenport FL', 'Haines City FL', 'Poinciana FL', 'St Cloud FL',
        'Deltona FL', 'DeLand FL', 'Lake Mary FL', 'Longwood FL',
        'Casselberry FL', 'Winter Springs FL', 'Oviedo FL'
    ]
    
    print(f"Searching {len(queries)} business types across {len(locations)} locations")
    print(f"Total searches: {len(queries) * len(locations)}")
    print(f"Estimated time: 5-15 minutes\n")
    
    # Generate leads
    leads = generator.generate_leads(queries, locations)
    
    if leads:
        # Save to Excel
        filename = generator.save_to_excel(leads)
        print(f"\n✅ COMPLETE: Found {len(leads)} businesses without websites!")
        print(f"📁 File saved: {filename}")
    else:
        print("No leads found.")
    
    print(f"\n{'='*60}")
    print(f"✅ Lead Generation Complete")
    print(f"{'='*60}\n")
    
    input("Press Enter to close...")


if __name__ == "__main__":
    main()
