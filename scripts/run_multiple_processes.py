import subprocess
for i in range(10):
    print('\nRun', i+1)
    subprocess.run(['python','workers/process_once.py'])
