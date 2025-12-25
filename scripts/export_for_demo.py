"""
Export crawl results for Platinum Finding Services demo
Generates structured JSON output for frontend consumption
"""
import sqlite3
import json
from collections import defaultdict
from datetime import datetime

DB_PATH = 'mcp_memory.db'

def export_results():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Get all memory entries grouped by namespace
    cur.execute("""
        SELECT namespace, key, value 
        FROM memory 
        ORDER BY namespace, id DESC
    """)
    
    data_by_namespace = defaultdict(list)
    
    for row in cur.fetchall():
        namespace, key, value_json = row
        try:
            value = json.loads(value_json)
            data_by_namespace[namespace].append({
                'url': key,
                'content': value
            })
        except:
            pass
    
    # Get job stats
    cur.execute("""
        SELECT 
            status,
            COUNT(*) as count,
            SUM(CASE WHEN result LIKE '%count%' THEN CAST(json_extract(result, '$.count') AS INTEGER) ELSE 0 END) as total_pages
        FROM jobs
        WHERE action = 'crawl/start'
        GROUP BY status
    """)
    
    job_stats = {}
    for row in cur.fetchall():
        status, count, pages = row
        job_stats[status] = {'jobs': count, 'pages': pages or 0}
    
    # Build output
    output = {
        'generated_at': datetime.now().isoformat(),
        'summary': {
            'total_namespaces': len(data_by_namespace),
            'total_urls_crawled': sum(len(v) for v in data_by_namespace.values()),
            'job_stats': job_stats
        },
        'data_sources': {}
    }
    
    # Group by category
    categories = {
        'business_loans': [],
        'real_estate': [],
        'social_sentiment': [],
        'county_records': [],
        'news': []
    }
    
    for ns, entries in data_by_namespace.items():
        # Categorize
        if any(x in ns for x in ['sba', 'ucc', 'biz', 'econ', 'chamber']):
            cat = 'business_loans'
        elif any(x in ns for x in ['pa', 'foreclosure', 'tax', 'permit', 'code']):
            cat = 'real_estate'
        elif any(x in ns for x in ['reddit', 'twitter', 'facebook', 'youtube']):
            cat = 'social_sentiment'
        elif any(x in ns for x in ['court', 'clerk']):
            cat = 'county_records'
        elif 'news' in ns:
            cat = 'news'
        else:
            cat = 'business_loans'  # default
        
        categories[cat].append({
            'namespace': ns,
            'url_count': len(entries),
            'sample_urls': [e['url'] for e in entries[:5]]
        })
    
    output['categories'] = categories
    
    # Top sources by volume
    top_sources = sorted(
        [(ns, len(entries)) for ns, entries in data_by_namespace.items()],
        key=lambda x: x[1],
        reverse=True
    )[:20]
    
    output['top_sources'] = [
        {'namespace': ns, 'url_count': count}
        for ns, count in top_sources
    ]
    
    conn.close()
    
    # Write output
    with open('platinum_demo_export.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✓ Exported {output['summary']['total_urls_crawled']} URLs across {output['summary']['total_namespaces']} sources")
    print(f"✓ Categories: {', '.join(f'{k}={len(v)} sources' for k,v in categories.items() if v)}")
    print(f"✓ Output: platinum_demo_export.json")
    
    return output

if __name__ == '__main__':
    export_results()
