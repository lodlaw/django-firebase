import os

import firebase_admin

SERVICE_ACCOUNT_ENV_VAR_PREFIX = 'APP_FIREBASE_SERVICE_ACCOUNT_'


def make_service_account_envar_name(name):
    return SERVICE_ACCOUNT_ENV_VAR_PREFIX + name


def initialize():
    private_key = os.environ[make_service_account_envar_name('PRIVATE_KEY')]
    if private_key[0] == '"' and private_key[-1] == '"':
        private_key = private_key[1:-1]

    config = f"""
    {{
    "type": "{os.environ[make_service_account_envar_name('TYPE')]}",
        "project_id": "{os.environ[make_service_account_envar_name('PROJECT_ID')]}",
        "private_key_id": "{os.environ[make_service_account_envar_name('PRIVATE_KEY_ID')]}",
        "private_key": "{private_key}",
        "client_email": "{os.environ[make_service_account_envar_name('CLIENT_EMAIL')]}",
        "client_id": "{os.environ[make_service_account_envar_name('CLIENT_ID')]}",
        "auth_uri": "{os.environ[make_service_account_envar_name('AUTH_URI')]}",
        "token_uri": "{os.environ[make_service_account_envar_name('TOKEN_URI')]}",
        "auth_provider_x509_cert_url": "{os.environ[make_service_account_envar_name('AUTH_PROVIDER_X509_CERT_URL')]}",
        "client_x509_cert_url": "{os.environ[make_service_account_envar_name('CLIENT_X509_CERT_URL')]}"
    }}
    """

    path = './cred.json'
    try:
        with open(path, 'w') as f:
            f.write(config)
            # json.dump(config, f)
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = path

        if not firebase_admin._apps:
            firebase_admin.initialize_app()
    finally:
        pass
