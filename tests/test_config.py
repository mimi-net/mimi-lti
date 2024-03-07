import os
import pathlib

from mimilti.config import RsaKey


config_folder = os.path.join(pathlib.Path(__file__).parent, "config")
rsa_public_path = os.path.join(config_folder, "public.key")
rsa_private_path = os.path.join(config_folder, "private.key")
config_path = os.path.join(config_folder, "config.json")
rsa_key = RsaKey(rsa_private_path, rsa_public_path)
