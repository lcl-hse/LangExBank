from secret_data import editors


def check_auth(session):
    if session:
        if "username" in session:
            if session["username"] in editors:
                return True

    return False
