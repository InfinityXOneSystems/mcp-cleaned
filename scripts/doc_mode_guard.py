#!/usr/bin/env python3
"""Guard for doc-evolution mode changes.

To integrate: wrap /admin/doc/mode POST with a passphrase check and append audit log entries.
"""
import os
import datetime

AUDIT_LOG = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'doc_mode_audit.log'))
PASSPHRASE = os.environ.get('DOC_MODE_PASSPHRASE', 'CHANGE_ME')

def authorize(given):
    return given == PASSPHRASE

def log_change(user, new_mode, path_override=None):
    ts = datetime.datetime.utcnow().isoformat() + 'Z'
    entry = f"{ts}\t{user}\t{new_mode}\t{path_override or ''}\n"
    with open(AUDIT_LOG, 'a', encoding='utf-8') as f:
        f.write(entry)

def main():
    print('Doc mode guard stub. Import and call authorize() + log_change().')

if __name__ == '__main__':
    main()
