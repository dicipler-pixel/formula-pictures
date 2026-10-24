"""Join transport parts and verify the exact original MP4 before publishing.
Normally run automatically by the one-purpose GitHub Actions workflow.
"""
from pathlib import Path
import hashlib,json,os
root=Path(__file__).resolve().parent
manifest_path=root/'video-upload.json'
if not manifest_path.exists():
 print('No pending video upload.')
 raise SystemExit(0)
m=json.loads(manifest_path.read_text())
output=root/m['filename']
assert output.parent==root and output.suffix=='.mp4'
tmp=output.with_suffix('.assembling')
h=hashlib.sha256();total=0
try:
 with tmp.open('wb') as out:
  for part in m['parts']:
   path=root/part['path']
   assert path.parent==root/'.upload'
   data=path.read_bytes()
   assert len(data)==part['size']
   assert hashlib.sha256(data).hexdigest()==part['sha256']
   out.write(data);h.update(data);total+=len(data)
 assert total==m['size'] and h.hexdigest()==m['sha256']
 os.replace(tmp,output)
finally:
 tmp.unlink(missing_ok=True)
print('Verified full-quality video:',output.name,total,'bytes',h.hexdigest())
