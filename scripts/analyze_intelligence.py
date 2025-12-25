"""
Analyze intelligence data from memory database
"""
import sqlite3
import json
from collections import defaultdict

DB_PATH = 'mcp_memory.db'

def analyze_sources():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all memory records with URLs
    cursor.execute("""
        SELECT id, key, value 
        FROM memory 
        WHERE value LIKE '%url%'
        LIMIT 1500
    """)
    
    records = cursor.fetchall()
    
    categories = defaultdict(lambda: defaultdict(list))
    url_count = 0
    
    for record_id, key, value in records:
        try:
            data = json.loads(value) if value else {}
            url = data.get('url', '')
            
            if not url:
                continue
                
            url_count += 1
            
            # Categorize based on URL patterns
            if 'sba.gov' in url or 'uccfilings' in url or 'chamber' in url.lower() or 'business' in url.lower():
                if 'sba.gov' in url:
                    categories['Business Loans']['SBA'].append({'url': url, 'id': record_id})
                elif 'ucc' in url.lower():
                    categories['Business Loans']['UCC Filings'].append({'url': url, 'id': record_id})
                elif 'chamber' in url.lower():
                    categories['Business Loans']['Chambers of Commerce'].append({'url': url, 'id': record_id})
                else:
                    categories['Business Loans']['Business Licenses'].append({'url': url, 'id': record_id})
                    
            elif 'property' in url.lower() or 'real' in url.lower() or 'foreclosure' in url.lower() or 'permit' in url.lower():
                if 'foreclosure' in url.lower():
                    categories['Real Estate']['Foreclosures'].append({'url': url, 'id': record_id})
                elif 'permit' in url.lower():
                    categories['Real Estate']['Building Permits'].append({'url': url, 'id': record_id})
                elif 'violation' in url.lower():
                    categories['Real Estate']['Code Violations'].append({'url': url, 'id': record_id})
                else:
                    categories['Real Estate']['Property Records'].append({'url': url, 'id': record_id})
                    
            elif 'biggerpockets' in url.lower() or 'reddit' in url.lower() or 'twitter' in url.lower():
                if 'biggerpockets' in url.lower():
                    categories['Social Sentiment']['BiggerPockets'].append({'url': url, 'id': record_id})
                elif 'reddit' in url.lower():
                    categories['Social Sentiment']['Reddit'].append({'url': url, 'id': record_id})
                else:
                    categories['Social Sentiment']['Twitter'].append({'url': url, 'id': record_id})
                    
            elif 'court' in url.lower() or 'lien' in url.lower() or 'filing' in url.lower():
                if 'lien' in url.lower():
                    categories['County Records']['Liens'].append({'url': url, 'id': record_id})
                else:
                    categories['County Records']['Court Filings'].append({'url': url, 'id': record_id})
                    
            elif 'news' in url.lower() or 'journal' in url.lower() or 'times' in url.lower():
                categories['News']['Local Business News'].append({'url': url, 'id': record_id})
                
            elif 'gofundme' in url.lower():
                categories['Crowdfunding']['GoFundMe'].append({'url': url, 'id': record_id})
                
        except json.JSONDecodeError:
            pass
    
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"INTELLIGENCE SOURCE ANALYSIS")
    print(f"{'='*60}\n")
    print(f"Total URLs found: {url_count}\n")
    
    for category, subcategories in sorted(categories.items()):
        print(f"\n{category}:")
        for subcat, urls in sorted(subcategories.items()):
            print(f"  └─ {subcat}: {len(urls)} URLs")
    
    print(f"\n{'='*60}\n")
    
    return dict(categories)

if __name__ == '__main__':
    categories = analyze_sources()
    
    # Export to JSON
    output = {
        'total_sources': sum(len(subcats) for subcats in categories.values()),
        'categories': {
            cat: {
                subcat: len(urls) 
                for subcat, urls in subcats.items()
            }
            for cat, subcats in categories.items()
        }
    }
    
    with open('intelligence_sources.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print("Exported to intelligence_sources.json")
