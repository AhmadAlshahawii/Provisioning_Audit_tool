import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "excludes": ["unittest", "demos"],
    "include_msvcr": True
}

bdist_msi_options = {
    "upgrade_code": "{0C5A5512-669B-4F14-B7BE-A2B44310DAB9}",
    "summary_data": {
            "author": "Ahmad ElShahawi"
    }
}

# base="Win32GUI" should be used only for Windows GUI app
base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="proaudit",
    version="2.3",
    description="Provisioning Audit tool",
    options={
            "build_exe": build_exe_options,
            "bdist_msi": bdist_msi_options,
            },
    executables=[
            Executable("parse.py",
                        target_name="Provisioning_Audit_Tool.exe",
                        base="Console",
                        copyright="Copyright (C) 2023 Ahmad ElShahawi",
                        shortcut_name="Provisioning Audit tool",
                        shortcut_dir="ProgramMenuFolder"
                       )
                ],
)