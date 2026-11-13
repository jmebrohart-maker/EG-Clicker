"""Ship Python and dependency license notices beside the frozen application."""
import importlib.metadata as metadata
from pathlib import Path
import shutil
import hashlib
import sys

output=Path(sys.argv[1])/'THIRD-PARTY-LICENSES'
output.mkdir(parents=True,exist_ok=True)
packages=('pycaw','comtypes','psutil','pyinstaller','pyinstaller-hooks-contrib','altgraph','pefile','pywin32-ctypes','packaging','setuptools','pillow')
summary=[]
for name in packages:
    distribution=metadata.distribution(name)
    summary.append(f'{distribution.metadata["Name"]} {distribution.version}: {distribution.metadata.get("License-Expression") or distribution.metadata.get("License") or "See included notices"}')
    for file in distribution.files or ():
        if file.name.lower().startswith(('license','copying','notice')):
            source=Path(distribution.locate_file(file))
            if source.is_file():
                suffix=hashlib.sha256(str(file).encode()).hexdigest()[:8]
                target=output/name/(file.name+'-'+suffix+'.txt');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
for name in ('LICENSE.txt','LICENSE'):
    source=Path(sys.base_prefix)/name
    if source.is_file():shutil.copy2(source,output/'Python-LICENSE.txt')
for source in (Path(sys.base_prefix)/'tcl').glob('*/license.terms'):
    shutil.copy2(source,output/f'{source.parent.name}-license.terms')
(output/'DEPENDENCIES.txt').write_text('\n'.join(summary)+'\n',encoding='utf-8')
