"""Use the installed NX translator without touching an interactive NX session."""
import json
import os
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parent


def find_nx():
    candidates=[]
    for key in ('LAMPSHADE_NX_DIR','UGII_BASE_DIR'):
        if os.environ.get(key):candidates.append(Path(os.environ[key]))
    siemens=Path(os.environ.get('ProgramFiles',r'C:\Program Files'))/'Siemens'
    if siemens.is_dir():
        candidates.extend(sorted(siemens.glob('NX*'),key=lambda p:p.name,reverse=True))
    for base in candidates:
        if (base/'NXBIN'/'run_journal.exe').is_file() and (base/'TRANSLATORS'/'step242'/'step242ug.def').is_file():return base
    return None


def nx_status():
    base=find_nx()
    return dict(available=base is not None,version=base.name if base else None)


def parasolid_export(solid,folder,fmt,target):
    from exports import cad_export
    folder=Path(folder)
    source=folder/'source.step'
    cad_export(solid,source,'step',target)
    return translate_step(source,folder,fmt,target=target)


def translate_step(source,folder,fmt,target=None,components=None):
    """Translate a checked STEP, including multiple simple chandelier components."""
    if fmt not in ('x_b','x_t'):raise ValueError('Choose a Parasolid binary or text file.')
    base=find_nx()
    if not base:raise ValueError('Parasolid export needs a local Siemens NX installation. Use STEP on this computer.')
    folder=Path(folder)
    output=folder/f'model.{fmt}';report_path=folder/'validation.json'
    config=dict(input=str(source),output=str(output),report=str(report_path))
    if components is not None:config['components']=components
    else:config['target']=list(target)
    config_path=folder/'job.json';config_path.write_text(json.dumps(config),encoding='utf-8')
    env=os.environ.copy()
    env['UGII_BASE_DIR']=str(base);env['UGII_ROOT_DIR']=str(base/'NXBIN')
    command=[str(base/'NXBIN'/'run_journal.exe'),str(ROOT/'nx_translate.py'),'-args',str(config_path)]
    flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
    started=time.perf_counter()
    with (folder/'nx.log').open('wb') as log:
        process=subprocess.Popen(command,cwd=folder,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=flags)
        try:process.wait(timeout=300)
        except subprocess.TimeoutExpired:
            # Stop only this export's process tree; never an existing interactive NX session.
            if os.name=='nt':subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=flags)
            else:process.kill()
            process.wait(timeout=15)
            raise ValueError('NX conversion exceeded five minutes. Try a simpler shade or use STEP.')
    if not report_path.is_file():
        raise ValueError('NX could not start the converter. Check that NX and its license are available, then retry.')
    report=json.loads(report_path.read_text(encoding='utf-8'))
    (ROOT/'exports').mkdir(exist_ok=True)
    (ROOT/'exports'/'last-nx-translation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    if process.returncode or not report.get('ok') or not output.is_file():
        (ROOT/'exports'/'last-nx-failure.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        detail=report.get('error','The NX converter did not finish.')
        raise ValueError(f'NX export failed: {detail}')
    report.update(nxVersion=base.name,format=fmt,conversionSeconds=round(time.perf_counter()-started,3))
    # Keep concise, non-sensitive evidence from the most recent successful conversion.
    (ROOT/'exports').mkdir(exist_ok=True)
    (ROOT/'exports'/'last-nx-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return output.read_bytes(),report
