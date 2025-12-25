"""
Google Sheets Integration for Asset Predictive Intelligence
Syncs predictions and outcomes with tracking spreadsheet
"""
import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    print("⚠️  Google API libraries not installed. Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")

from prediction_engine import get_stats, init_predictions_table
import sqlite3

# Spreadsheet ID from URL
SPREADSHEET_ID = "14geQJz48lBe64is7qoOIZFMJQHgPE53PbOZkS8w3WsA"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def get_sheets_service():
    """Initialize Google Sheets API service"""
    if not GOOGLE_AVAILABLE:
        raise Exception("Google API libraries not available")
    
    # Try to use service account credentials
    creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if creds_path and os.path.exists(creds_path):
        creds = service_account.Credentials.from_service_account_file(
            creds_path, scopes=SCOPES
        )
    else:
        raise Exception("GOOGLE_APPLICATION_CREDENTIALS not set or file not found")
    
    service = build('sheets', 'v4', credentials=creds)
    return service.spreadsheets()


def export_predictions_to_sheet():
    """Export all predictions from DB to Google Sheet"""
    
    sheets = get_sheets_service()
    
    # Get all predictions from DB
    conn = sqlite3.connect('mcp_memory.db')
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, asset, asset_type, prediction_type, predicted_direction, 
               predicted_value, target_date, confidence, status, outcome,
               accuracy_score, made_at, rationale
        FROM predictions
        ORDER BY made_at DESC
    """)
    
    rows = cur.fetchall()
    conn.close()
    
    # Prepare data for sheet
    header = [
        'ID', 'Asset', 'Type', 'Prediction Type', 'Direction', 'Target Value',
        'Target Date', 'Confidence %', 'Status', 'Outcome', 'Accuracy Score',
        'Made At', 'Rationale'
    ]
    
    data = [header]
    for row in rows:
        data.append([
            row[0],  # id
            row[1],  # asset
            row[2],  # asset_type
            row[3],  # prediction_type
            row[4] or '',  # predicted_direction
            row[5] or '',  # predicted_value
            row[6],  # target_date
            row[7],  # confidence
            row[8],  # status
            row[9] or '',  # outcome
            row[10] or '',  # accuracy_score
            row[11],  # made_at
            (row[12] or '')[:100]  # rationale (truncated)
        ])
    
    # Write to sheet
    body = {'values': data}
    result = sheets.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range='Predictions!A1',
        valueInputOption='RAW',
        body=body
    ).execute()
    
    print(f"✓ Exported {len(data)-1} predictions to Google Sheet")
    print(f"  Updated {result.get('updatedCells')} cells")
    return result


def import_outcomes_from_sheet():
    """Import actual outcomes from Google Sheet to resolve predictions"""
    
    sheets = get_sheets_service()
    
    # Read outcomes sheet
    result = sheets.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='Outcomes!A2:E'  # ID, Actual Value, Actual Direction, Notes, Resolved Date
    ).execute()
    
    values = result.get('values', [])
    
    if not values:
        print("No outcomes to import")
        return
    
    conn = sqlite3.connect('mcp_memory.db')
    cur = conn.cursor()
    
    imported = 0
    for row in values:
        if len(row) < 2:
            continue
        
        pred_id = row[0]
        actual_value = float(row[1]) if len(row) > 1 and row[1] else None
        actual_direction = row[2] if len(row) > 2 else None
        notes = row[3] if len(row) > 3 else ''
        
        # Get original prediction
        cur.execute("""
            SELECT predicted_value, predicted_direction, confidence
            FROM predictions
            WHERE id = ? AND status = 'pending'
        """, (pred_id,))
        
        pred_row = cur.fetchone()
        if not pred_row:
            continue
        
        pred_value, pred_direction, confidence = pred_row
        
        # Calculate outcome
        outcome = 'unknown'
        accuracy_score = 0.0
        
        if pred_direction and actual_direction:
            if pred_direction.lower() == actual_direction.lower():
                outcome = 'correct'
                accuracy_score = confidence / 100.0
            else:
                outcome = 'incorrect'
                accuracy_score = 0.0
        
        if pred_value and actual_value:
            error_pct = abs((actual_value - pred_value) / pred_value) * 100
            if error_pct < 5:
                outcome = 'correct'
                accuracy_score = (confidence / 100.0) * (1 - error_pct / 5)
            elif error_pct < 10:
                outcome = 'partial'
                accuracy_score = (confidence / 100.0) * 0.5
            else:
                outcome = 'incorrect'
                accuracy_score = 0.0
        
        # Update prediction
        resolved_at = datetime.now().isoformat()
        cur.execute("""
            UPDATE predictions
            SET actual_value = ?, actual_direction = ?, outcome = ?,
                accuracy_score = ?, resolved_at = ?, status = 'resolved'
            WHERE id = ?
        """, (actual_value, actual_direction, outcome, accuracy_score, resolved_at, pred_id))
        
        imported += 1
    
    conn.commit()
    conn.close()
    
    print(f"✓ Imported {imported} outcomes from Google Sheet")
    return imported


def sync_stats_to_sheet():
    """Update summary stats in Google Sheet"""
    
    sheets = get_sheets_service()
    stats = get_stats()
    
    # Prepare stats data
    data = [
        ['Metric', 'Value'],
        ['Total Predictions', stats['total_predictions']],
        ['Pending', stats['pending']],
        ['Resolved', stats['resolved']],
        ['Correct', stats['correct']],
        ['Partial', stats['partial']],
        ['Accuracy Rate', f"{stats['accuracy_rate']:.1f}%"],
        ['Avg Accuracy Score', f"{stats['avg_accuracy_score']:.3f}"],
        ['Avg Confidence', f"{stats['avg_confidence']:.1f}%"],
        ['Last Updated', datetime.now().isoformat()]
    ]
    
    body = {'values': data}
    result = sheets.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range='Stats!A1',
        valueInputOption='RAW',
        body=body
    ).execute()
    
    print(f"✓ Updated stats in Google Sheet")
    return result


def full_sync():
    """Complete two-way sync: export predictions, import outcomes, update stats"""
    print("\n🔄 Starting full sync with Google Sheet...\n")
    
    try:
        export_predictions_to_sheet()
        print()
        import_outcomes_from_sheet()
        print()
        sync_stats_to_sheet()
        print("\n✅ Full sync complete\n")
    except Exception as e:
        print(f"\n❌ Sync failed: {e}\n")
        if "GOOGLE_APPLICATION_CREDENTIALS" in str(e):
            print("💡 Set up Google Sheets access:")
            print("   1. Create service account at https://console.cloud.google.com")
            print("   2. Download JSON key file")
            print("   3. Set environment variable: $env:GOOGLE_APPLICATION_CREDENTIALS='path/to/key.json'")
            print("   4. Share the spreadsheet with the service account email")


if __name__ == '__main__':
    init_predictions_table()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'export':
            export_predictions_to_sheet()
        elif cmd == 'import':
            import_outcomes_from_sheet()
        elif cmd == 'stats':
            sync_stats_to_sheet()
        elif cmd == 'sync':
            full_sync()
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: python sheets_sync.py [export|import|stats|sync]")
    else:
        full_sync()
