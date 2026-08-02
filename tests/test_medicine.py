"""tests/test_medicine.py – Medicine management tests."""
import pytest, uuid
from datetime import date


def uid():
    from services.auth_service import register_user
    u = f"med_{uuid.uuid4().hex[:8]}"
    r = register_user(u, f"{u}@ex.com", "Pass1234!")
    return r["user_id"]


class TestAddMedicine:
    def test_add_basic(self):
        from services.medicine_service import add_medicine, get_medicines
        user_id = uid()
        r = add_medicine(user_id, "Metformin", "500mg", "Twice daily", ["08:00","20:00"], "After food")
        assert r["success"] is True
        m = get_medicines(user_id)
        assert len(m) == 1 and m[0]["name"] == "Metformin"

    def test_no_name_fails(self):
        from services.medicine_service import add_medicine
        r = add_medicine(uid(), "", "500mg", "Once daily", ["08:00"])
        assert r["success"] is False

    def test_no_times_fails(self):
        from services.medicine_service import add_medicine
        r = add_medicine(uid(), "Aspirin", "75mg", "Once daily", [])
        assert r["success"] is False

    def test_times_parsed_as_list(self):
        from services.medicine_service import add_medicine, get_medicines
        user_id = uid()
        add_medicine(user_id, "Vit D", "1000IU", "Twice daily", ["09:00","21:00"])
        m = get_medicines(user_id)
        assert isinstance(m[0]["times"], list) and "09:00" in m[0]["times"]

    def test_multiple_medicines(self):
        from services.medicine_service import add_medicine, get_medicines
        user_id = uid()
        for name in ["Med A", "Med B", "Med C"]:
            add_medicine(user_id, name, "10mg", "Once daily", ["08:00"])
        assert len(get_medicines(user_id)) == 3


class TestUpdateDeleteMedicine:
    @pytest.fixture(autouse=True)
    def setup(self):
        from services.medicine_service import add_medicine
        self.uid = uid()
        r = add_medicine(self.uid, "OldName", "100mg", "Once daily", ["09:00"])
        self.mid = r["medicine_id"]

    def test_update(self):
        from services.medicine_service import update_medicine, get_medicine
        r = update_medicine(self.mid, "NewName", "200mg", "Twice daily",
                            ["08:00","20:00"], "Before food")
        assert r["success"] is True
        m = get_medicine(self.mid)
        assert m["name"] == "NewName" and "08:00" in m["times"]

    def test_soft_delete(self):
        from services.medicine_service import delete_medicine, get_medicines
        delete_medicine(self.mid)
        active = get_medicines(self.uid, active_only=True)
        assert all(m["id"] != self.mid for m in active)

    def test_deleted_still_exists_inactive(self):
        from services.medicine_service import delete_medicine, get_medicines
        delete_medicine(self.mid)
        all_m = get_medicines(self.uid, active_only=False)
        assert any(m["id"] == self.mid for m in all_m)


class TestAdherence:
    @pytest.fixture(autouse=True)
    def setup(self):
        from services.medicine_service import add_medicine
        self.uid = uid()
        r = add_medicine(self.uid, "Vitamin D", "1000IU", "Once daily", ["08:00"])
        self.mid = r["medicine_id"]
        self.scheduled = f"{date.today().isoformat()} 08:00"

    def test_mark_taken(self):
        from services.medicine_service import log_medicine_taken, get_medicine_logs
        r = log_medicine_taken(self.uid, self.mid, self.scheduled)
        assert r["success"] is True
        logs = get_medicine_logs(self.uid, days=1)
        assert any(l["status"] == "taken" for l in logs)

    def test_cannot_mark_taken_twice(self):
        from services.medicine_service import log_medicine_taken
        log_medicine_taken(self.uid, self.mid, self.scheduled)
        r = log_medicine_taken(self.uid, self.mid, self.scheduled)
        assert r["success"] is False

    def test_adherence_100_after_taken(self):
        from services.medicine_service import log_medicine_taken, get_adherence_stats
        log_medicine_taken(self.uid, self.mid, self.scheduled)
        s = get_adherence_stats(self.uid, days=1)
        assert s["taken"] >= 1 and s["adherence_pct"] == 100.0

    def test_adherence_zero_no_logs(self):
        from services.medicine_service import get_adherence_stats
        s = get_adherence_stats(uid(), days=7)
        assert s["adherence_pct"] == 0 and s["total"] == 0


class TestTodaySchedule:
    def test_three_time_slots(self):
        from services.medicine_service import add_medicine, get_today_medicines
        user_id = uid()
        add_medicine(user_id, "MultiDose", "500mg", "Three times daily",
                     ["08:00","13:00","21:00"])
        today = get_today_medicines(user_id)
        assert len(today) == 3

    def test_default_status_pending(self):
        from services.medicine_service import add_medicine, get_today_medicines
        user_id = uid()
        add_medicine(user_id, "PendMed", "10mg", "Once daily", ["07:00"])
        today = get_today_medicines(user_id)
        assert today[0]["status"] == "pending"
