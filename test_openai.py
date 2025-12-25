import os
from openai_helper import chat

def main():
    key = os.getenv('OPENAI_API_KEY')
    if not key:
        print('SKIP: OPENAI_API_KEY not set')
        return

    res = chat([
        { 'role': 'user', 'content': 'Respond with exactly one word: Hello' }
    ], model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'))
    print(res)

if __name__ == '__main__':
    main()
