import os
import shutil
import site
import sys

if len(sys.argv) < 2:
    print("Example usage: python patch_django.py src")
    exit(1)

folder = sys.argv[1]
site_packages = site.getsitepackages()[0]
packages = ['django', 'asgiref', 'sqlparse']

for package in packages:
    if not os.path.exists(os.path.join(folder, package)):
        shutil.copytree(os.path.join(site_packages, package), os.path.join(folder, package))

patches = [
    {
        'path': 'django/utils/timezone.py',
        'old': 'return zoneinfo.ZoneInfo(settings.TIME_ZONE)',
        'new': 'return timezone(timedelta(hours=0))'
    },
    {
        'path': 'django/utils/translation/__init__.py',
        'old': 'return _trans.gettext(message)',
        'new': 'return message'
    },
    {
        'path': 'django/core/handlers/asgi.py',
        'old': 'asyncio.create_task(self.listen_for_disconnect(receive)),',
        'new': ''
    },
    {
        'path': 'django/core/handlers/asgi.py',
        'old': 'response = tasks[1].result()',
        'new': 'pass'
    },
    {
        'path': 'django/core/handlers/asgi.py',
        'old': 'await sync_to_async(response.close)()',
        'new': 'pass'
    },
]

for patch in patches:
    path = os.path.join(folder, patch['path'])

    with open(path, 'r') as file:
        filedata = file.read()

    # Replace the target string
    filedata = filedata.replace(patch['old'], patch['new'])

    # Write the file out again
    with open(path, 'w') as file:
        file.write(filedata)

# Create gitignore
path = os.path.join(folder, '.gitignore')

try:
    with open(path, 'r') as file:
        filedata = file.read()
except:
    filedata = ''

for package in packages:
    if package not in filedata:
        filedata += '\n' + package

with open(path, 'w') as file:
    file.write(filedata)

print('Django patched!')
