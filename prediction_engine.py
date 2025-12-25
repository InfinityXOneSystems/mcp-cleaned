"""
Infinity X Intelligence - Prediction Engine
Logs predictions, tracks outcomes, calculates accuracy over time
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Literal

DB_PATH = 'mcp_memory.db'

def init_predictions_table():
    """Create predictions table if it doesn't exist"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            prediction_type TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            target_date TEXT NOT NULL,
            predicted_value REAL,
            predicted_direction TEXT,
            confidence INTEGER,
            rationale TEXT,
            data_sources TEXT,
            made_at TEXT NOT NULL,
            actual_value REAL,
            actual_direction TEXT,
            outcome TEXT,
            accuracy_score REAL,
            resolved_at TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)
    
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_predictions_status ON predictions(status)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_predictions_target ON predictions(target_date)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_predictions_asset ON predictions(asset)
    """)
    
    conn.commit()
    conn.close()
    print("✓ Predictions table initialized")


def log_prediction(
    asset: str,
    asset_type: Literal['crypto', 'stock', 'forex', 'commodity', 'index'],
    prediction_type: Literal['price', 'direction', 'volatility', 'event'],
    timeframe: str,
    target_date: str,
    predicted_value: float = None,
    predicted_direction: Literal['up', 'down', 'sideways', 'breakout'] = None,
    confidence: int = 50,
    rationale: str = "",
    data_sources: list = None
) -> int:
    """
    Log a new prediction
    
    Args:
        asset: Ticker/symbol (BTC, TSLA, EUR/USD, etc.)
        asset_type: Category of asset
        prediction_type: What we're predicting
        timeframe: How long (24h, 7d, 30d, 90d, etc.)
        target_date: ISO date when prediction resolves
        predicted_value: Specific price/value target (optional)
        predicted_direction: Direction prediction
        confidence: 0-100 confidence score
        rationale: Why we think this
        data_sources: List of data sources used
    
    Returns:
        prediction_id
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    made_at = datetime.now().isoformat()
    
    cur.execute("""
        INSERT INTO predictions (
            asset, asset_type, prediction_type, timeframe, target_date,
            predicted_value, predicted_direction, confidence, rationale,
            data_sources, made_at, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
    """, (
        asset, asset_type, prediction_type, timeframe, target_date,
        predicted_value, predicted_direction, confidence, rationale,
        json.dumps(data_sources or []), made_at
    ))
    
    prediction_id = cur.lastrowid
    conn.commit()
    conn.close()
    
    print(f"✓ Prediction #{prediction_id} logged: {asset} {predicted_direction or predicted_value} by {target_date} ({confidence}% confidence)")
    return prediction_id


def resolve_prediction(
    prediction_id: int,
    actual_value: float = None,
    actual_direction: str = None
):
    """Mark a prediction as resolved and calculate accuracy"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Get original prediction
    cur.execute("SELECT predicted_value, predicted_direction, confidence FROM predictions WHERE id = ?", (prediction_id,))
    row = cur.fetchone()
    if not row:
        print(f"✗ Prediction #{prediction_id} not found")
        conn.close()
        return
    
    pred_value, pred_direction, confidence = row
    
    # Calculate outcome
    outcome = 'unknown'
    accuracy_score = 0.0
    
    if pred_direction and actual_direction:
        if pred_direction == actual_direction:
            outcome = 'correct'
            accuracy_score = confidence / 100.0
        else:
            outcome = 'incorrect'
            accuracy_score = 0.0
    
    if pred_value and actual_value:
        # Price prediction accuracy (% error)
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
    
    resolved_at = datetime.now().isoformat()
    
    cur.execute("""
        UPDATE predictions
        SET actual_value = ?, actual_direction = ?, outcome = ?,
            accuracy_score = ?, resolved_at = ?, status = 'resolved'
        WHERE id = ?
    """, (actual_value, actual_direction, outcome, accuracy_score, resolved_at, prediction_id))
    
    conn.commit()
    conn.close()
    
    print(f"✓ Prediction #{prediction_id} resolved: {outcome} (score: {accuracy_score:.2f})")


def get_stats():
    """Get overall prediction accuracy stats"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved,
            SUM(CASE WHEN outcome = 'correct' THEN 1 ELSE 0 END) as correct,
            SUM(CASE WHEN outcome = 'partial' THEN 1 ELSE 0 END) as partial,
            AVG(CASE WHEN status = 'resolved' THEN accuracy_score ELSE NULL END) as avg_score,
            AVG(confidence) as avg_confidence
        FROM predictions
    """)
    
    row = cur.fetchone()
    total, resolved, correct, partial, avg_score, avg_conf = row
    
    stats = {
        'total_predictions': total or 0,
        'resolved': resolved or 0,
        'pending': (total or 0) - (resolved or 0),
        'correct': correct or 0,
        'partial': partial or 0,
        'accuracy_rate': (correct / resolved * 100) if resolved else 0,
        'avg_accuracy_score': avg_score or 0,
        'avg_confidence': avg_conf or 0
    }
    
    conn.close()
    return stats


def list_pending(days_ahead: int = 7):
    """List predictions resolving in next N days"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cutoff = (datetime.now() + timedelta(days=days_ahead)).isoformat()
    
    cur.execute("""
        SELECT id, asset, predicted_direction, predicted_value, target_date, confidence
        FROM predictions
        WHERE status = 'pending' AND target_date <= ?
        ORDER BY target_date ASC
    """, (cutoff,))
    
    pending = []
    for row in cur.fetchall():
        pending.append({
            'id': row[0],
            'asset': row[1],
            'direction': row[2],
            'value': row[3],
            'target': row[4],
            'confidence': row[5]
        })
    
    conn.close()
    return pending


if __name__ == '__main__':
    init_predictions_table()
    print("\n📊 Current Stats:")
    stats = get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v:.1f}" if isinstance(v, float) else f"  {k}: {v}")
