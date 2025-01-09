import os
import shutil

SOURCE_DIR = './deploy'
TARGET_DIR = 'SUNI.app/Contents/runtime'

if os.path.exists(TARGET_DIR):
    shutil.rmtree(TARGET_DIR)

shutil.copytree(SOURCE_DIR, TARGET_DIR, ignore=shutil.ignore_patterns('*.svn','*.iss','*.dll'))


