"""
Google Sheets and Calendar Integration
"""
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Scopes
SHEETS_SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar']
COMBINED_SCOPES = SHEETS_SCOPES + CALENDAR_SCOPES

def get_credentials(scopes: List[str]):
    """Get Google API credentials from service account JSON"""
    creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if not creds_path:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not set")
    return service_account.Credentials.from_service_account_file(creds_path, scopes=scopes)

def get_sheets_service():
    """Get Google Sheets API service"""
    creds = get_credentials(SHEETS_SCOPES)
    return build('sheets', 'v4', credentials=creds)

def get_calendar_service():
    """Get Google Calendar API service"""
    creds = get_credentials(CALENDAR_SCOPES)
    return build('calendar', 'v3', credentials=creds)

# ===== SHEETS OPERATIONS =====

def sheets_append_rows(sheet_id: str, range_name: str, values: List[List[Any]]) -> dict:
    """Append rows to a Google Sheet"""
    try:
        service = get_sheets_service()
        body = {'values': values}
        result = service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        return {
            'success': True,
            'updated_cells': result.get('updates', {}).get('updatedCells', 0),
            'updated_range': result.get('updates', {}).get('updatedRange')
        }
    except HttpError as e:
        return {'success': False, 'error': str(e)}

def sheets_read_range(sheet_id: str, range_name: str) -> dict:
    """Read values from a Google Sheet range"""
    try:
        service = get_sheets_service()
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=range_name
        ).execute()
        values = result.get('values', [])
        return {
            'success': True,
            'values': values,
            'count': len(values)
        }
    except HttpError as e:
        return {'success': False, 'error': str(e)}

def sheets_update_range(sheet_id: str, range_name: str, values: List[List[Any]]) -> dict:
    """Update values in a Google Sheet range"""
    try:
        service = get_sheets_service()
        body = {'values': values}
        result = service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        return {
            'success': True,
            'updated_cells': result.get('updatedCells', 0),
            'updated_range': result.get('updatedRange')
        }
    except HttpError as e:
        return {'success': False, 'error': str(e)}

def sheets_clear_range(sheet_id: str, range_name: str) -> dict:
    """Clear values in a Google Sheet range"""
    try:
        service = get_sheets_service()
        service.spreadsheets().values().clear(
            spreadsheetId=sheet_id,
            range=range_name
        ).execute()
        return {'success': True}
    except HttpError as e:
        return {'success': False, 'error': str(e)}

def sheets_create_sheet(sheet_id: str, title: str) -> dict:
    """Create a new sheet (tab) in an existing spreadsheet"""
    try:
        service = get_sheets_service()
        request = {
            'addSheet': {
                'properties': {'title': title}
            }
        }
        body = {'requests': [request]}
        result = service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body=body
        ).execute()
        return {
            'success': True,
            'sheet_id': result['replies'][0]['addSheet']['properties']['sheetId']
        }
    except HttpError as e:
        return {'success': False, 'error': str(e)}

# ===== CALENDAR OPERATIONS =====

def calendar_list_events(calendar_id: str = 'primary', max_results: int = 10, time_min: Optional[str] = None) -> dict:
    """List calendar events"""
    try:
        service = get_calendar_service()
        if not time_min:
            time_min = datetime.now(timezone.utc).isoformat()
        
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        return {
            'success': True,
            'events': events,
            'count': len(events)
        }
    except HttpError as e:
        return {'success': False, 'error': str(e)}

def calendar_create_event(
    calendar_id: str,
    summary: str,
    start_time: str,
    end_time: str,
    description: Optional[str] = None,
    location: Optional[str] = None
) -> dict:
    """Create a calendar event"""
    try:
        service = get_calendar_service()
        event = {
            'summary': summary,
            'start': {'dateTime': start_time, 'timeZone': 'UTC'},
            'end': {'dateTime': end_time, 'timeZone': 'UTC'}
        }
        if description:
            event['description'] = description
        if location:
            event['location'] = location
        
        result = service.events().insert(calendarId=calendar_id, body=event).execute()
        return {
            'success': True,
            'event_id': result.get('id'),
            'html_link': result.get('htmlLink')
        }
    except HttpError as e:
        return {'success': False, 'error': str(e)}

def calendar_update_event(
    calendar_id: str,
    event_id: str,
    summary: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    description: Optional[str] = None
) -> dict:
    """Update a calendar event"""
    try:
        service = get_calendar_service()
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        
        if summary:
            event['summary'] = summary
        if start_time:
            event['start'] = {'dateTime': start_time, 'timeZone': 'UTC'}
        if end_time:
            event['end'] = {'dateTime': end_time, 'timeZone': 'UTC'}
        if description:
            event['description'] = description
        
        result = service.events().update(calendarId=calendar_id, eventId=event_id, body=event).execute()
        return {
            'success': True,
            'event_id': result.get('id'),
            'html_link': result.get('htmlLink')
        }
    except HttpError as e:
        return {'success': False, 'error': str(e)}

def calendar_delete_event(calendar_id: str, event_id: str) -> dict:
    """Delete a calendar event"""
    try:
        service = get_calendar_service()
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        return {'success': True}
    except HttpError as e:
        return {'success': False, 'error': str(e)}

# ===== HELPER FUNCTIONS =====

def log_prediction_to_sheet(sheet_id: str, prediction_data: Dict[str, Any]) -> dict:
    """Log a prediction to Google Sheets"""
    timestamp = datetime.now().isoformat()
    row = [
        timestamp,
        prediction_data.get('asset', ''),
        prediction_data.get('prediction_type', ''),
        prediction_data.get('predicted_value', ''),
        prediction_data.get('confidence', ''),
        prediction_data.get('status', 'pending')
    ]
    return sheets_append_rows(sheet_id, 'Predictions!A:F', [row])

def log_crawl_to_sheet(sheet_id: str, crawl_data: Dict[str, Any]) -> dict:
    """Log crawl results to Google Sheets"""
    timestamp = datetime.now().isoformat()
    row = [
        timestamp,
        crawl_data.get('url', ''),
        crawl_data.get('pages_crawled', 0),
        crawl_data.get('status', 'completed'),
        json.dumps(crawl_data.get('metadata', {}))
    ]
    return sheets_append_rows(sheet_id, 'Crawls!A:E', [row])

def create_event_from_prediction(calendar_id: str, prediction_data: Dict[str, Any]) -> dict:
    """Create a calendar event for a prediction target date"""
    target_date = prediction_data.get('target_date')
    if not target_date:
        return {'success': False, 'error': 'No target_date provided'}
    
    # Parse target date and create event window
    try:
        dt = datetime.fromisoformat(target_date.replace('Z', '+00:00'))
    except:
        dt = datetime.strptime(target_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    
    start_time = dt.isoformat()
    end_time = (dt + timedelta(hours=1)).isoformat()
    
    summary = f"Prediction: {prediction_data.get('asset', 'Unknown')} - {prediction_data.get('prediction_type', 'price')}"
    description = f"Confidence: {prediction_data.get('confidence', 50)}%\nPredicted: {prediction_data.get('predicted_value', 'N/A')}"
    
    return calendar_create_event(calendar_id, summary, start_time, end_time, description)
