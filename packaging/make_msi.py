"""Generate explicit per-user MSI components, including folder cleanup."""
import hashlib
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

root = Path(__file__).resolve().parents[1]
payload = root / 'dist' / 'OpenDownload'
out = root / 'packaging'
out.mkdir(exist_ok=True)
(root / 'release').mkdir(exist_ok=True)
ns = 'http://wixtoolset.org/schemas/v4/wxs'
ui = 'http://wixtoolset.org/schemas/v4/wxs/ui'
ET.register_namespace('',ns)
ET.register_namespace('ui',ui)


def node(parent, tag, **attributes):
    return ET.SubElement(parent, '{'+ns+'}'+tag, attributes)


def ident(prefix, value):
    return prefix+hashlib.sha256(value.encode()).hexdigest()[:24]


wix = ET.Element('{'+ns+'}Wix')
package = node(wix,'Package',Name='OpenDownload',Manufacturer='OpenDownload',Version='0.2.0',
               UpgradeCode='CDFF6423-9AA3-42D3-B13B-58E24C471DF7',Scope='perUser',InstallerVersion='500',Compressed='yes')
node(package,'MajorUpgrade',DowngradeErrorMessage='A newer version of OpenDownload is already installed.')
node(package,'MediaTemplate',EmbedCab='yes',CompressionLevel='high')
node(package,'Icon',Id='AppIcon',SourceFile=str(root/'assets'/'OpenDownload.ico'))
node(package,'Property',Id='ARPPRODUCTICON',Value='AppIcon')
node(package,'Property',Id='WIXUI_EXITDIALOGOPTIONALTEXT',Value='OpenDownload is ready. Open it from your desktop or Start menu.')
ET.SubElement(package,'{'+ui+'}WixUI',{'Id':'WixUI_InstallDir','InstallDirectory':'INSTALLFOLDER'})
# Go directly from Welcome to location selection; no invented license agreement.
custom_ui=node(package,'UI')
node(custom_ui,'Publish',Dialog='WelcomeDlg',Control='Next',Event='NewDialog',Value='InstallDirDlg',Order='5',Condition='NOT Installed')
node(custom_ui,'Publish',Dialog='InstallDirDlg',Control='Back',Event='NewDialog',Value='WelcomeDlg',Order='5',Condition='1')
local=node(package,'StandardDirectory',Id='LocalAppDataFolder')
programs=node(local,'Directory',Id='LocalPrograms',Name='Programs')
install=node(programs,'Directory',Id='INSTALLFOLDER',Name='OpenDownload')
directories={Path('.'):install}
feature=node(package,'Feature',Id='Application',Title='OpenDownload',Level='1')
for directory in sorted({p.parent.relative_to(payload) for p in payload.rglob('*') if p.is_file()},key=lambda p:(len(p.parts),str(p))):
    current=Path('.')
    for part in directory.parts:
        child=current/part
        if child not in directories:
            directories[child]=node(directories[current],'Directory',Id=ident('D',str(child)),Name=part)
        current=child
    component_id=ident('C',str(directory))
    component=node(directories[directory],'Component',Id=component_id,
                   Guid=str(uuid.uuid5(uuid.UUID('cdff6423-9aa3-42d3-b13b-58e24c471df7'),str(directory))))
    node(component,'RegistryValue',Root='HKCU',Key='Software\\OpenDownload\\Installer',Name=component_id,
         Type='integer',Value='1',KeyPath='yes')
    node(component,'RemoveFolder',Id=ident('R',str(directory)),On='uninstall')
    for file in sorted((payload/directory).iterdir()):
        if file.is_file():
            relative=file.relative_to(payload)
            node(component,'File',Id='MainExe' if str(relative)=='OpenDownload.exe' else ident('F',str(relative)),Source=str(file))
    node(feature,'ComponentRef',Id=component_id)
menu=node(package,'StandardDirectory',Id='ProgramMenuFolder')
folder=node(menu,'Directory',Id='ApplicationMenuFolder',Name='OpenDownload')
node(package,'StandardDirectory',Id='DesktopFolder')
shortcuts=node(folder,'Component',Id='Shortcuts',Guid='E97C4AF3-E807-4B67-8CE2-F6AC4C32CC55')
node(shortcuts,'RegistryValue',Root='HKCU',Key='Software\\OpenDownload\\Installer',Name='Shortcuts',Type='integer',Value='1',KeyPath='yes')
node(shortcuts,'RemoveFolder',Id='RemoveStartMenu',On='uninstall')
for shortcut_id,directory_id in [('StartMenuShortcut','ApplicationMenuFolder'),('DesktopShortcut','DesktopFolder')]:
    node(shortcuts,'Shortcut',Id=shortcut_id,Directory=directory_id,Name='OpenDownload',
         Target='[#MainExe]',WorkingDirectory='INSTALLFOLDER',Icon='AppIcon',Description='OpenDownload Download Manager')
node(feature,'ComponentRef',Id='Shortcuts')
ET.indent(wix,space='  ')
ET.ElementTree(wix).write(out/'OpenDownload.wxs',encoding='utf-8',xml_declaration=True)
print('Generated installer source for',sum(p.is_file() for p in payload.rglob('*')),'files')
