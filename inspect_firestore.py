#!/usr/bin/env python3
import os, sys, traceback

def main():
    try:
        from google.cloud import firestore
    except Exception as e:
        print('ERROR: google.cloud.firestore import failed:', e)
        traceback.print_exc()
        return 2

    project = os.environ.get('FIRESTORE_PROJECT') or os.environ.get('FIRESTORE_PROJECT_ID') or 'infinity-x-one-systems'
    print('Using Firestore project:', project)
    try:
        client = firestore.Client(project=project)
    except Exception as e:
        print('ERROR: Failed to create Firestore client:')
        traceback.print_exc()
        return 3

    try:
        print('\nCollections:')
        cols = list(client.collections())
        if not cols:
            print('  (no collections found or no permission to list)')
        for c in cols:
            try:
                print(' -', c.id)
            except Exception:
                pass

        target = 'mcp_memory'
        print(f"\nInspecting collection '{target}':")
        coll_ref = client.collection(target)
        docs = list(coll_ref.limit(50).stream())
        if not docs:
            print('  (no documents found in collection)')
            return 0
        for d in docs:
            try:
                data = d.to_dict()
                keys = list(data.keys())
                print(f" - doc id: {d.id} | top-level keys: {keys}")
            except Exception as e:
                print(' - doc id:', d.id, ' (failed to read):', e)
        return 0
    except Exception as e:
        print('ERROR: Failed during collection/doc listing:')
        traceback.print_exc()
        return 4

if __name__ == '__main__':
    sys.exit(main())
