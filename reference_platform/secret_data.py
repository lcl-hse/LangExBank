import os

## Login/password pairs for content editors
editors = {
    os.getenv('REF_EDITOR_LOGIN', default='Editor'):
        os.getenv('REF_EDITOR_PASSWORD', default='iamtheeditor')
}

secret_key = os.getenv('REF_SECRET_KEY', default='xsv6p2k5')
