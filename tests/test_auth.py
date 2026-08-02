"""tests/test_auth.py – Authentication service tests."""
import pytest


def _unique(prefix):
    import uuid
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class TestPasswordHashing:
    def test_hash_differs_from_plain(self):
        from authentication.auth import hash_password
        assert hash_password("MyPassword123") != "MyPassword123"

    def test_verify_correct(self):
        from authentication.auth import hash_password, verify_password
        h = hash_password("SecretPass!")
        assert verify_password("SecretPass!", h) is True

    def test_verify_wrong(self):
        from authentication.auth import hash_password, verify_password
        h = hash_password("CorrectPassword")
        assert verify_password("WrongPassword", h) is False

    def test_different_hashes_for_same_password(self):
        from authentication.auth import hash_password
        assert hash_password("SamePassword") != hash_password("SamePassword")

    def test_verify_empty_string(self):
        from authentication.auth import hash_password, verify_password
        assert verify_password("", hash_password("password123")) is False


class TestRegistration:
    def test_successful_registration(self):
        from services.auth_service import register_user
        r = register_user(_unique("user"), f"{_unique('u')}@ex.com", "Password123")
        assert r["success"] is True

    def test_duplicate_username_rejected(self):
        from services.auth_service import register_user
        uname = _unique("dup")
        register_user(uname, f"{_unique('dup')}@ex.com", "Password123")
        r = register_user(uname, f"{_unique('other')}@ex.com", "Password123")
        assert r["success"] is False

    def test_duplicate_email_rejected(self):
        from services.auth_service import register_user
        email = f"{_unique('same')}@ex.com"
        register_user(_unique("user1"), email, "Password123")
        r = register_user(_unique("user2"), email, "Password123")
        assert r["success"] is False

    def test_short_username_rejected(self):
        from services.auth_service import register_user
        r = register_user("ab", f"{_unique('ab')}@ex.com", "Password123")
        assert r["success"] is False

    def test_invalid_email_rejected(self):
        from services.auth_service import register_user
        r = register_user(_unique("u"), "not-an-email", "Password123")
        assert r["success"] is False

    def test_short_password_rejected(self):
        from services.auth_service import register_user
        r = register_user(_unique("u"), f"{_unique('u')}@ex.com", "short")
        assert r["success"] is False

    def test_full_registration(self):
        from services.auth_service import register_user
        r = register_user(_unique("full"), f"{_unique('full')}@ex.com",
                          "Password123", full_name="Ramesh Kumar", age=68)
        assert r["success"] is True


class TestLogin:
    @pytest.fixture(autouse=True)
    def create_user(self):
        from services.auth_service import register_user
        self.uname = _unique("login")
        self.email = f"{self.uname}@ex.com"
        register_user(self.uname, self.email, "ValidPass123", full_name="Login User")

    def test_login_with_username(self):
        from services.auth_service import login_user
        r = login_user(self.uname, "ValidPass123")
        assert r["success"] is True

    def test_login_with_email(self):
        from services.auth_service import login_user
        r = login_user(self.email, "ValidPass123")
        assert r["success"] is True

    def test_wrong_password_fails(self):
        from services.auth_service import login_user
        r = login_user(self.uname, "WrongPassword")
        assert r["success"] is False

    def test_nonexistent_user_fails(self):
        from services.auth_service import login_user
        r = login_user("nobody_xyz", "anypassword")
        assert r["success"] is False

    def test_case_insensitive_username(self):
        from services.auth_service import login_user
        r = login_user(self.uname.upper(), "ValidPass123")
        assert r["success"] is True


class TestProfile:
    @pytest.fixture(autouse=True)
    def create_user(self):
        from services.auth_service import register_user
        uname = _unique("prof")
        r = register_user(uname, f"{uname}@ex.com", "Pass1234!")
        self.uid = r["user_id"]

    def test_update_profile(self):
        from services.auth_service import update_profile, get_user
        update_profile(self.uid, full_name="New Name", age=70)
        user = get_user(self.uid)
        assert user["full_name"] == "New Name"

    def test_change_password_success(self):
        from services.auth_service import change_password, login_user, get_user
        u = get_user(self.uid)
        r = change_password(self.uid, "Pass1234!", "NewPassword99!")
        assert r["success"] is True

    def test_change_password_wrong_old(self):
        from services.auth_service import change_password
        r = change_password(self.uid, "WrongOld", "NewPassword99!")
        assert r["success"] is False


class TestEmergencyContacts:
    @pytest.fixture(autouse=True)
    def create_user(self):
        from services.auth_service import register_user
        uname = _unique("emcon")
        r = register_user(uname, f"{uname}@ex.com", "EmPass123!")
        self.uid = r["user_id"]

    def test_add_contact(self):
        from services.auth_service import add_emergency_contact, get_emergency_contacts
        r = add_emergency_contact(self.uid, "Priya", "Daughter", "+919876543210")
        assert r["success"] is True
        assert len(get_emergency_contacts(self.uid)) >= 1

    def test_add_contact_without_phone_fails(self):
        from services.auth_service import add_emergency_contact
        r = add_emergency_contact(self.uid, "Rahul", "Son", "")
        assert r["success"] is False

    def test_delete_contact(self):
        from services.auth_service import add_emergency_contact, delete_emergency_contact, get_emergency_contacts
        add_emergency_contact(self.uid, "Delete Me", "Test", "+910000000001")
        contacts = get_emergency_contacts(self.uid)
        cid = contacts[-1]["id"]
        delete_emergency_contact(cid)
        remaining_ids = [c["id"] for c in get_emergency_contacts(self.uid)]
        assert cid not in remaining_ids
