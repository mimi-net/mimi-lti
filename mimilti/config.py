import copy
import json
from collections import defaultdict


class RsaKey:

    def __init__(self, private_key_path: str, public_key_path: str):

        with open(public_key_path, "rb") as public_key_file:
            self._public_key = public_key_file.read()

        with open(private_key_path, "rb") as private_key_file:
            self._private_key = private_key_file.read()

    @property
    def public_key(self) -> bytes:
        return self._public_key

    @property
    def private_key(self) -> bytes:
        return self._private_key

    def __eq__(self, other: "RsaKey") -> bool:
        return (
            self._public_key == other.public_key
            and self._private_key == other.private_key
        )


class ToolConfig:

    def __init__(self, config):
        self._config = config

    @property
    def config(self) -> dict:
        return self._config

    def get_jwks_endpoint(self) -> str:
        return self._config["jwks_endpoint"]

    def get_client_id(self) -> str:
        return self._config["aud"]


class Config:

    def __init__(self, config_path: str, rsa_key: RsaKey) -> None:
        self._config_path = config_path
        self._config = {}
        self._tools: dict[str, list[ToolConfig]] = defaultdict(list)
        self._rsa_key = rsa_key

        with open(self._config_path, "r") as file:
            self._config = json.load(file)

        issuers = self._config["issuers"]

        for issuer in issuers:
            tools = issuers[issuer]["tools"]

            for tool in tools:
                self._tools[issuer].append(ToolConfig(tool))

    def get_tool(self, issuer: str, aud: str) -> ToolConfig | None:

        if issuer not in self.get_issuers():
            return None

        for tool in self._tools[issuer]:
            if tool.get_client_id() == aud:
                return tool

        return None

    def get_login_url(self, issuer: str) -> str:
        return self._config["issuers"][issuer]["login_url"]

    def get_token_url(self, issuer: str) -> str:
        return self._config["issuers"][issuer]["token_url"]

    def add_tool(self, iss: str, aud: str) -> ToolConfig | None:

        if (tool := self.get_tool(iss, aud)) is not None:
            return tool

        if iss in self._tools:
            tools = self._tools[iss]
            exist_tool = tools[0]
            exist_tool_config = exist_tool.config
            exist_tool_aud = exist_tool.get_client_id()

            new_tool_config = copy.deepcopy(exist_tool_config)
            for key, value in new_tool_config.items():
                if exist_tool_aud in value:
                    new_tool_config[key] = value.replace(exist_tool_aud, aud)

            tool = ToolConfig(new_tool_config)
            tools.append(tool)
            self._config["issuers"][iss]["tools"].append(new_tool_config)
            with open(self._config_path, "w") as file:
                file.write(json.dumps(self._config))

        return None

    def get_keys_and_kid(self) -> tuple[RsaKey, str]:
        kid = self._config["kid"]
        return self._rsa_key, kid

    def is_trusted_issuer(self, issuer: str) -> bool:
        return issuer in self._config["issuers"]

    def get_issuers(self) -> tuple[str]:
        return tuple(self._config["issuers"])

    def get_tools(self, issuer: str) -> list[ToolConfig]:
        return self._tools[issuer]

    def generate_template_endpoint(self, issuer: str, aud: str) -> str:
        if issuer in self._tools:
            tools = self._tools[issuer]
            exist_tool = tools[0]
            exist_aud = exist_tool.get_client_id()
            return exist_tool.get_jwks_endpoint().replace(exist_aud, aud)
