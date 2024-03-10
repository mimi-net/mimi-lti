# mimi-lti
Implementation of the LTI1.3 protocol

## Prerequisites:
[Python 3.12+](https://www.python.org/downloads/)

## JSON Web Key Set
The LTI1.3 protocol uses JSON Web Tokens with signatures to exchange messages between the LMS (Learning management system) and an external tool. It is necessary to generate a public and private RSA Key, as well as a jwks endpoint that the LMS will access.

Generate an RSA key:

```
mimilti.utils.keygen --path='path_to_save_rsa_key' --jwk-path='path_to_save_json_web_key'
```

Configure the JWKS endpoint (example for Flask):
```python
from flask import send_from_directory, Flask
from mimilti.lms_pool import LmsRequestsPool
from mimilti.config import Config, RsaKey

app = Flask(__name__)
key = RsaKey(private_key_path, public_key_path)
config = Config(public_json_path, key)
LmsRequestsPool.start(config)

@app.route("/jwks", methods=["GET"])
def jwks():
    return send_from_directory(
        os.path.join(path_where_json_web_key_was_saved), "jwk.json")
```

## Login endpoint

Configure the login endpoint:
```python
@app.route("/login", methods=["POST"])
def login():
      if request.method == "POST":
      session_service = SessionDataStorage()
      # We receive an authorization request from the lms
      try:
          request_object = LtiRequestObject(request.form, session_service, config)
      except Exception as e:
          return jsonify({"error": str(e)}), 401

      # Redirecting the request back to the lms to receive the jwt token
      redirect_url = request_object.get_redirect_url()
      issuer = request_object.get_issuer()


      session_service.iss = issuer
      session_service.aud = request_object.get_client_id()

      return redirect(redirect_url)
```

## Launch endpoint

Configure the launch endpoint (redirection after login):
```python
@app.route("/launch", methods=["POST"])
def launch():
  if request.method == "POST":
        session_data_service = SessionDataStorage()
        request_object = LtiRequestObject(request.form, session_data_service, config)
  
        try:
            # We check that the token is signed and other details
            data = request_object.get_token()

            # Save info about user
            session_data_service.update_params(data)

            # Adding the trusted tool
            config.add_tool(session_data_service.iss, session_data_service.aud)
        except Exception as e:
            return jsonify({"error": str(e)}), 401

        # you login logic
        return redirect(url_for("index"))
```

## The logic of requests to the LMS
The library is designed to process requests only from trusted and pre-configured LMS.

### Config

```python
key = RsaKey(private_key_path, public_key_path)
config = Config(public_json_path, key)
```
You need to set up a json file with information about the jwks endpoint, login and auth url (this information must be provided by the lms admin).
At the same time, subsequent tools will be added automatically, and the jwks endpoint will be generated depending on the previous value (for example, blackboard creates its own point for each application, which depends on the tool id, while the default moodle does not do this).
```
# public_json_path
{
    "kid": "5r03KaCiqaQBVD8zwDu0mHmd0WXxxwBAoG67SpSyD50",
    "issuers": {
        "http://localhost/moodle": {
            "login_url": "http://localhost/moodle/mod/lti/auth.php",
            "token_url": "http://localhost/moodle/mod/lti/token.php",
            "tools": [
                {
                    "aud": "DS7jNSEoKQPjFCk",
                    "jwks_endpoint": "http://localhost/moodle/mod/lti/certs.php"
                },
                {
                    "aud": "URw5NjQzGdD2KdE",
                    "jwks_endpoint": "http://localhost/moodle/mod/lti/certs.php"
                }
            ]
        }
    }
}
```
### Caching 
#### MimiSession
The simplest wrapper over requests.Session to implement caching without changing requests interface.
```python
import datetime
from mimilti.cache_adapter import MimiSession, CacheAdapter

s = MimiSession()
expires = datetime.timedelta(seconds=3600)
cache_adapter = CacheAdapter()
s.mount("http://localhost/moodle/mod/lti/token.php", cache_adapter)
# The request will be cached
s.get('http://localhost/moodle/mod/lti/token.php')
```

#### TTL LRU Cache
LRU Cache with TTL. It is possible to configure a specific ttl for each function.
```python
import datetime
import mimilti.cache_adapter.LruCache

lru_cache = LruCache()

@lru_cache.ttl_lru_cache() # without expires
def get_x(x: int) -> int:
  return x

@lru_cache.ttl_lru_cache(datetime.timedelta(hours=1)) #with expires
def get_y(y: int) -> int:
  return y
```
### Data storage
The LMS sends information about the current context to the jwt (user role, external user id, ...). To store this information, SessionDataStorage is implemented, which stores information in the Flask session. However, this approach may seem wrong, since all information is sent to the server with each request and creates a load. You can implement the DataStorage and SessionStorage interface. For example, by storing information in a database.

### Working with grades
When you insert an external tool into the course, a scale for grading immediately appears. Depending on your desire, you can rate new scales (or use an already created one).

Set the progress to the default scale:
```python

from mimilti.grade import GradeService, CompletedFullyGradedProgress
from mimilti.data_storage import SessionDataStorage

grade_service = GradeService(SessionDataStorage(), config, refresh=True)
progress = CompletedFullyGradedProgress(
    score_given=60,
    score_maximum=100,
    comment="comment",
    timestamp=datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
)
```

Set the progress to the specific scale:

```python
guid = "7262dd22-ae2b-4a88-8d29-dfcf728b2c11"
grade_service = get_grade_service()
progress = CompletedFullyGradedProgress(
    score_given=60,
    score_maximum=100,
    comment="comment",
    timestamp=datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
)

grade_service.set_grade(progress, guid)
```
This is convenient because by using the guid of the task (for example, a test generated by an external tool), you can easily identify the scales to which you need to put the score (this is done using the resource_id field when creating a new scale).

### User Permissions
Limit the capabilities of the crawlers based on their role:

```python
from mimilti.grade import LineItem, CompletedFullyGradedProgress
from mimilti.data_storage import SessionDataStorage
from mimilti.roles import ContextInstructorRole, RoleService

def get_role_service():
    data_service = SessionDataStorage()
    role_service = RoleService(data_service)
    return role_service

@get_role_service().lti_role_accepted(ContextInstructorRole)
def create_test():
    test_guid = "7262dd22-ae2b-4a88-8d29-dfcf728b2c11"
    test_label = "test label"
    test_tag = "test tag"
    test_maximum_score = 100
    test_start_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    test_end_time = (datetime.now() + timedelta(seconds=3600)).strftime(
        "%Y-%m-%dT%H:%M:%S"
    )

    data_service = SessionDataStorage()
    grade_service = GradeService(data_service, config)
    lineitem = LineItem(
        id=None,
        label=test_label,
        score_maximum=test_maximum_score,
        resource_id=test_guid,
        tag=test_tag,
        start_date_time=test_start_time,
        end_date_time=test_end_time,
    )

    grade_service.create_or_set_lineitem(lineitem)
```
In this case, the test can be created by LMS users with the role of Instructor or higher (for example, Admin).
