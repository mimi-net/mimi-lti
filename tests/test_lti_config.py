from mimilti.config import Config

from test_config import rsa_key, config_path


def get_issuers(self) -> str:
    return self._config.keys()


def test_config():
    config = Config(config_path, rsa_key)

    iss = "http://localhost/moodle"

    kid = "5r03KaCiqaQBVD8zwDu0mHmd0WXxxwBAoG67SpSyD50"
    config_rsa_key, config_kid = config.get_keys_and_kid()

    assert rsa_key == config_rsa_key
    assert kid == config_kid

    # aud not defined
    non_existent_aud = "non_existent_aud"
    tool = config.get_tool(iss, non_existent_aud)

    assert tool is None

    tool = config.get_tool(iss, "asdasdasdfrfrfrfrfrfrfrfrre")

    assert config.get_login_url(iss) == "http://localhost/moodle/mod/lti/auth.php"
    assert config.get_token_url(iss) == "http://localhost/moodle/mod/lti/token.php"
    assert tool.get_jwks_endpoint() == "http://localhost/moodle/mod/lti/certs.php"
    assert tool.get_client_id() == "asdasdasdfrfrfrfrfrfrfrfrre"

    assert config.is_trusted_issuer(iss)
    assert config.get_issuers() == ("http://localhost/moodle",)
