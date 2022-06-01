import firebase_admin
from firebase_admin.auth import UserNotFoundError


class AuthProvider:
    def forward(self, user):
        """
        Signs in an user to an external system
        :param user: an user to provide auth for
        :type user: django.contrib.auth.models.User
        :return: the system credentials upon success
        """
        raise NotImplementedError()


class FirebaseAuthProvider(AuthProvider):
    def forward(self, user):
        """
        Signs in an user to an external system
        :param user: an user to provide auth for
        :type user: django.contrib.auth.models.User
        :return: the system credentials upon success
        """
        self._sign_out_firebase_user(user)

        firebase_login_token = self._create_firebase_login_token(user)

        return {
            'firebase_auth_token': firebase_login_token
        }

    @classmethod
    def _sign_out_firebase_user(cls, user):
        try:
            firebase_admin.auth.revoke_refresh_tokens(uid=user.email)
        except UserNotFoundError:
            pass

    @classmethod
    def _create_firebase_login_token(cls, user):
        try:
            firebase_admin.auth.create_user(uid=str(user.uuid), email=user.email)
        except:
            firebase_admin._auth_utils.UidAlreadyExistsError

        return firebase_admin.auth.create_custom_token(uid=str(user.uuid)).decode("utf-8")
