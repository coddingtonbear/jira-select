# -*- mode: python ; coding: utf-8 -*-
from io import StringIO
import os
import pkg_resources
from PyInstaller.utils.hooks import copy_metadata
import subprocess

import requirements

DO_NOT_PACKAGE = [
    'pyinstaller',
    'pyinstaller_hooks_contrib',
]


block_cipher = None


def Entrypoint(dist, group, name, **kwargs):
    import pkg_resources

    # get toplevel packages of distribution from metadata
    def get_toplevel(dist):
        distribution = pkg_resources.get_distribution(dist)
        if distribution.has_metadata("top_level.txt"):
            return list(distribution.get_metadata("top_level.txt").split())
        else:
            return []

    kwargs.setdefault("hiddenimports", [])
    packages = []
    for distribution in kwargs["hiddenimports"]:
        packages += get_toplevel(distribution)

    all_entrypoints = pkg_resources.get_entry_map("jira-select")
    for entrypoint_group, entrypoint_map in all_entrypoints.items():
        if not entrypoint_group.startswith("jira_select."):
            continue

        for entrypoint_name, entrypoint in entrypoint_map.items():
            packages.append(entrypoint.resolve().__module__)

    kwargs.setdefault("pathex", [])
    # get the entry point
    ep = pkg_resources.get_entry_info(dist, group, name)
    # insert path of the egg at the verify front of the search path
    kwargs["pathex"] = [ep.dist.location] + kwargs["pathex"]
    # script name must not be a valid module name to avoid name clashes on import
    script_path = os.path.join(workpath, name + "-script.py")
    print("creating script for entry point", dist, group, name)
    with open(script_path, "w") as fh:
        print("import", ep.module_name, file=fh)
        for package in packages:
            print("import", package, file=fh)
        print("%s.%s()" % (ep.module_name, ".".join(ep.attrs)), file=fh)

    datas = []
    installed_packages = subprocess.check_output(["pip", "freeze"])
    for req in requirements.parse(installed_packages.decode('utf-8')):
        if req.name not in DO_NOT_PACKAGE:
            try:
                datas += copy_metadata(req.name)
            except pkg_resources.DistributionNotFound:
                print(f"Could not find {req.name}")

    kwargs['datas'] = datas

    return Analysis([script_path] + kwargs.get("scripts", []), **kwargs)


a = Entrypoint(
    "jira-select",
    "console_scripts",
    "jira-select",
    pathex=[
        os.getcwd(),
        os.path.join(os.getcwd(), "env/lib/python3.9/site-packages/"),
    ],
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    # a.binaries,
    # Ja.zipfiles,
    # a.datas,
    [],
    exclude_binaries=True,  # added
    name="jira-select",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    # upx_exclude=[],
    # runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="jira-select",
)
