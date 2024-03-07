import os
import json
import click
from jwcrypto.jwk import JWK
from Crypto.PublicKey import RSA


def generate_keys(key_directory_path: str, jwk_directory_path: str) -> None:
    os.makedirs(key_directory_path, exist_ok=True)
    os.makedirs(jwk_directory_path, exist_ok=True)

    key = RSA.generate(4096)

    public_key = key.public_key().exportKey()
    private_key = key.exportKey()

    public_key_path = os.path.join(key_directory_path, "public.key")
    private_key_path = os.path.join(key_directory_path, "private.key")

    with open(public_key_path, "wb") as public, open(private_key_path, "wb") as private:
        public.write(public_key)
        private.write(private_key)

    jwk_obj = JWK.from_pem(public_key)
    public_jwk = json.loads(jwk_obj.export_public())
    public_jwk["alg"] = "RS256"
    public_jwk["use"] = "sig"

    public_json_path = os.path.join(jwk_directory_path, "jwk.json")
    with open(public_json_path, "w") as file:
        file.write(json.dumps(public_jwk))


@click.command()
@click.option(
    "--path", help="The path to the directory where to save the keys", required=True
)
@click.option(
    "--jwk-path",
    help="The path to the directory where to save json web key",
    required=True,
)
def key_generator(path, jwk_path) -> None:
    click.echo("Generating keys...")
    generate_keys(path, jwk_path)
    click.echo("Rsa key saved to {}".format(path))
    click.echo("JWK saved to {}".format(jwk_path))


if __name__ == "__main__":
    key_generator()
