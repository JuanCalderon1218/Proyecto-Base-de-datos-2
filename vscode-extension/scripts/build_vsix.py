#!/usr/bin/env python3
"""Empaqueta la extension sin dependencias, segun el formato VSIX de VS Code."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from xml.sax.saxutils import escape
import json
import mimetypes
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'package.json').read_text(encoding='utf-8'))
OUT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/(f"{manifest['name']}-{manifest['version']}.vsix")
packaged=['package.json','README.md','CHANGELOG.md','LICENSE','src/api.js','src/extension.js','src/view.js',
          'media/panel.css','media/panel.js','resources/icon.svg','resources/icon.png']
for f in packaged:
    if not (ROOT/f).is_file(): raise FileNotFoundError(ROOT/f)
xml_escape=lambda s:escape(str(s), {'"':'&quot;',"'":'&apos;'})
meta=f'''<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011" xmlns:d="http://schemas.microsoft.com/developer/vsx-schema-design/2011">
 <Metadata>
  <Identity Language="es-PE" Id="{xml_escape(manifest['name'])}" Version="{xml_escape(manifest['version'])}" Publisher="{xml_escape(manifest['publisher'])}"/>
  <DisplayName>{xml_escape(manifest['displayName'])}</DisplayName>
  <Description xml:space="preserve">{xml_escape(manifest['description'])}</Description>
  <Tags>NoSQL, MongoDB, FastAPI, alerts</Tags>
  <Categories>Other,Visualization</Categories>
  <GalleryFlags>Public</GalleryFlags>
  <Properties>
   <Property Id="Microsoft.VisualStudio.Code.Engine" Value="{xml_escape(manifest['engines']['vscode'])}"/>
   <Property Id="Microsoft.VisualStudio.Code.ExtensionDependencies" Value=""/>
   <Property Id="Microsoft.VisualStudio.Code.ExtensionPack" Value=""/>
   <Property Id="Microsoft.VisualStudio.Code.ExtensionKind" Value="ui"/>
   <Property Id="Microsoft.VisualStudio.Code.LocalizedLanguages" Value=""/>
   <Property Id="Microsoft.VisualStudio.Code.EnabledApiProposals" Value=""/>
   <Property Id="Microsoft.VisualStudio.Code.ExecutesCode" Value="true"/>
  </Properties>
 </Metadata>
 <Installation><InstallationTarget Id="Microsoft.VisualStudio.Code"/></Installation>
 <Dependencies/>
 <Assets><Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/>
 <Asset Type="Microsoft.VisualStudio.Services.Content.Details" Path="extension/README.md" Addressable="true"/>
 <Asset Type="Microsoft.VisualStudio.Services.Content.Changelog" Path="extension/CHANGELOG.md" Addressable="true"/>
 <Asset Type="Microsoft.VisualStudio.Services.Content.License" Path="extension/LICENSE" Addressable="true"/>
 <Asset Type="Microsoft.VisualStudio.Services.Icons.Default" Path="extension/resources/icon.png" Addressable="true"/></Assets>
</PackageManifest>'''
ct={
 '.json':'application/json','.vsixmanifest':'text/xml','.js':'application/javascript',
 '.css':'text/css','.svg':'image/svg+xml','.png':'image/png','.md':'text/markdown','.txt':'text/plain'
}
ct_xml='<?xml version="1.0" encoding="utf-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'+''.join(
    f'<Default Extension="{k}" ContentType="{v}"/>' for k,v in sorted(ct.items()))+'</Types>'
ET.fromstring(meta)
ET.fromstring(ct_xml)
OUT.parent.mkdir(parents=True,exist_ok=True)
with ZipFile(OUT,'w',compression=ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml',ct_xml)
    z.writestr('extension.vsixmanifest',meta)
    for f in packaged: z.write(ROOT/f,'extension/'+f)
with ZipFile(OUT) as z:
    assert z.testzip() is None
    assert 'extension/package.json' in z.namelist()
    assert 'extension/src/extension.js' in z.namelist()
    assert 'extension/README.md' in z.namelist()
    assert 'extension/resources/icon.png' in z.namelist()
    parsed=json.loads(z.read('extension/package.json'))
    assert parsed['main']=='./src/extension.js'
    assert parsed['contributes']['viewsContainers']['activitybar']
print(f'VSIX generado: {OUT} ({OUT.stat().st_size:,} bytes)')
