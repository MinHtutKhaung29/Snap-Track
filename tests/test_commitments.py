import json
import os
import re
import sys
import time
import unittest
import uuid
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))

from app.chat import service, tools as toolbox
from app.commitments import store
from app.shared import db


def make_user(label):
    email = "cmt-" + label + "-" + str(int(time.time() * 1000)) + "-" + uuid.uuid4().hex + "@example.invalid"
    return db.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
        ("commitment " + label, email, "x"),
    )


def count_rows(sql, params):
    return int(db.fetch_one(sql, params)["n"])


def csrf_value(html):
    match = re.search(r'name="csrf_token" value="([^"]+)"', html or "")
    return match.group(1) if match else ""


class CommitmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user_id = make_user("owner")
        cls.other_id = make_user("other")
        cls.category_id = db.fetch_one(
            "SELECT category_id FROM categories WHERE kind = 'expense' AND code = 'food'"
        )["category_id"]

    @classmethod
    def tearDownClass(cls):
        for uid in (cls.user_id, cls.other_id):
            db.execute("DELETE FROM chat_message WHERE user_id = %s", (uid,))
            db.execute("DELETE FROM transactions WHERE user_id = %s", (uid,))
            db.execute("DELETE FROM commitments WHERE user_id = %s", (uid,))
            db.execute("DELETE FROM users WHERE user_id = %s", (uid,))
        left = count_rows(
            "SELECT (SELECT COUNT(*) FROM users WHERE user_id IN (%s, %s)) + "
            "(SELECT COUNT(*) FROM commitments WHERE user_id IN (%s, %s)) + "
            "(SELECT COUNT(*) FROM transactions WHERE user_id IN (%s, %s)) + "
            "(SELECT COUNT(*) FROM chat_message WHERE user_id IN (%s, %s)) AS n",
            (cls.user_id, cls.other_id) * 4,
        )
        if left:
            raise AssertionError("leftover fixture rows: " + str(left))

    def create_bill(self, user_id, title, amount, due_day, start_date):
        with db.cursor(commit=True) as cur:
            return store.create_commitment(
                cur,
                user_id,
                {
                    "kind": "bill",
                    "title": title,
                    "amount": amount,
                    "total_amount": None,
                    "months": None,
                    "due_day": due_day,
                    "start_date": start_date,
                    "category_id": self.category_id,
                    "category_name": "食費",
                },
            )

    def create_installment(self, user_id, title, total, months, due_day, start_date):
        with db.cursor(commit=True) as cur:
            return store.create_commitment(
                cur,
                user_id,
                {
                    "kind": "installment",
                    "title": title,
                    "amount": total // months,
                    "total_amount": total,
                    "months": months,
                    "due_day": due_day,
                    "start_date": start_date,
                    "category_id": self.category_id,
                    "category_name": "食費",
                },
            )

    def pay(self, user_id, commitment_id, as_of):
        with db.cursor(commit=True) as cur:
            return store.mark_paid(cur, user_id, commitment_id, as_of=as_of)

    def commitment_row(self, commitment_id):
        return db.fetch_one(
            "SELECT paid_count, status, next_due_date, due_day FROM commitments WHERE commitment_id = %s",
            (commitment_id,),
        )

    def txn_count(self, user_id):
        return count_rows(
            "SELECT COUNT(*) AS n FROM transactions WHERE user_id = %s AND deleted_at IS NULL",
            (user_id,),
        )

    def test_due_date_clamping_january_february_march(self):
        bill = self.create_bill(self.user_id, "家賃 31日", 85000, 31, date(2027, 1, 1))
        self.assertEqual(bill["next_due_date"], date(2027, 1, 31))
        january = self.pay(self.user_id, bill["id"], date(2027, 1, 31))
        self.assertEqual(january["next_due_date"], "2027-02-28")
        february = self.pay(self.user_id, bill["id"], date(2027, 2, 28))
        self.assertEqual(february["next_due_date"], "2027-03-31")
        row = self.commitment_row(bill["id"])
        self.assertEqual(row["due_day"], 31)
        self.assertEqual(row["next_due_date"], date(2027, 3, 31))
        print(
            "due_day=31: 2027-01-31 -> "
            + january["next_due_date"]
            + " -> "
            + february["next_due_date"]
            + " (stored due_day="
            + str(row["due_day"])
            + ")"
        )

    def test_installment_remainder_sums_to_total(self):
        plan = self.create_installment(self.user_id, "冷蔵庫 6回払い", 100000, 6, 27, date(2026, 12, 1))
        self.assertEqual(plan["amount"], 16666)
        amounts = []
        for _ in range(6):
            due = self.commitment_row(plan["id"])["next_due_date"]
            amounts.append(self.pay(self.user_id, plan["id"], due)["amount"])
        self.assertEqual(amounts, [16666, 16666, 16666, 16666, 16666, 16670])
        self.assertEqual(sum(amounts), 100000)
        final = self.commitment_row(plan["id"])
        self.assertEqual((final["paid_count"], final["status"]), (6, "done"))
        self.assertEqual(final["next_due_date"], date(2027, 5, 27))
        live = db.fetch_one(
            "SELECT SUM(amount) AS total, COUNT(*) AS n FROM transactions "
            "WHERE user_id = %s AND commitment_id = %s AND deleted_at IS NULL",
            (self.user_id, plan["id"]),
        )
        self.assertEqual(int(live["total"]), 100000)
        self.assertEqual(int(live["n"]), 6)
        print("installment 100000/6: " + str(amounts) + " sum=" + str(sum(amounts)))

    def test_create_bill_writes_one_active_row_and_no_expense(self):
        before = self.txn_count(self.user_id)
        bill = self.create_bill(self.user_id, "通信費", 5000, 25, date(2026, 12, 1))
        row = db.fetch_one(
            "SELECT kind, status, paid_count, next_due_date, months, total_amount, due_day "
            "FROM commitments WHERE commitment_id = %s AND user_id = %s",
            (bill["id"], self.user_id),
        )
        self.assertEqual(row["kind"], "bill")
        self.assertEqual(row["status"], "active")
        self.assertEqual(int(row["paid_count"]), 0)
        self.assertEqual(row["next_due_date"], date(2026, 12, 25))
        self.assertIsNone(row["months"])
        self.assertIsNone(row["total_amount"])
        self.assertEqual(int(row["due_day"]), 25)
        self.assertEqual(self.txn_count(self.user_id), before)

    def test_mark_paid_writes_one_linked_transaction_and_advances(self):
        bill = self.create_bill(self.user_id, "電気代", 7800, 5, date(2026, 11, 1))
        before = self.txn_count(self.user_id)
        saved = self.pay(self.user_id, bill["id"], date(2026, 11, 20))
        txn = db.fetch_one(
            "SELECT user_id, commitment_id, kind, amount, txn_date, category_id, source_kind "
            "FROM transactions WHERE txn_id = %s",
            (saved["txn_id"],),
        )
        self.assertEqual(int(txn["user_id"]), self.user_id)
        self.assertEqual(int(txn["commitment_id"]), bill["id"])
        self.assertEqual(txn["kind"], "expense")
        self.assertEqual(int(txn["amount"]), 7800)
        self.assertEqual(txn["txn_date"], date(2026, 11, 20))
        self.assertEqual(int(txn["category_id"]), self.category_id)
        self.assertEqual(txn["source_kind"], "manual")
        self.assertEqual(self.txn_count(self.user_id), before + 1)
        row = self.commitment_row(bill["id"])
        self.assertEqual(int(row["paid_count"]), 1)
        self.assertEqual(row["status"], "active")
        self.assertEqual(row["next_due_date"], date(2026, 12, 5))

    def test_final_payment_marks_done_and_done_is_refused(self):
        plan = self.create_installment(self.user_id, "車検 2回払い", 50000, 2, 10, date(2026, 11, 1))
        self.pay(self.user_id, plan["id"], date(2026, 11, 10))
        last = self.pay(self.user_id, plan["id"], date(2026, 12, 10))
        self.assertEqual(last["status"], "done")
        row = self.commitment_row(plan["id"])
        self.assertEqual((int(row["paid_count"]), row["status"]), (2, "done"))
        self.assertEqual(row["next_due_date"], date(2026, 12, 10))
        before = self.txn_count(self.user_id)
        with self.assertRaises(store.CommitmentError) as caught:
            self.pay(self.user_id, plan["id"], date(2027, 1, 10))
        self.assertEqual(str(caught.exception), "commitment is not active")
        self.assertEqual(self.txn_count(self.user_id), before)

    def test_undo_restores_paid_count_and_due_date(self):
        bill = self.create_bill(self.user_id, "水道代", 4200, 10, date(2026, 11, 1))
        saved = self.pay(self.user_id, bill["id"], date(2026, 11, 10))
        self.assertEqual(int(self.commitment_row(bill["id"])["paid_count"]), 1)
        self.assertEqual(service.undo_transaction(self.user_id, saved["txn_id"]), "undone")
        row = self.commitment_row(bill["id"])
        self.assertEqual(int(row["paid_count"]), 0)
        self.assertEqual(row["status"], "active")
        self.assertEqual(row["next_due_date"], date(2026, 11, 10))
        txn = db.fetch_one("SELECT deleted_at FROM transactions WHERE txn_id = %s", (saved["txn_id"],))
        self.assertIsNotNone(txn["deleted_at"])
        self.assertEqual(service.undo_transaction(self.user_id, saved["txn_id"]), "ignored")

    def test_foreign_commitment_is_refused(self):
        foreign = self.create_bill(self.other_id, "他人の家賃", 90000, 27, date(2026, 11, 1))
        before = self.txn_count(self.user_id)
        with self.assertRaises(store.CommitmentError) as caught:
            self.pay(self.user_id, foreign["id"], date(2026, 12, 1))
        self.assertEqual(str(caught.exception), "commitment not found")
        self.assertEqual(self.txn_count(self.user_id), before)
        row = self.commitment_row(foreign["id"])
        self.assertEqual((int(row["paid_count"]), row["status"]), (0, "active"))

    def test_tool_declarations_and_strict_validation(self):
        self.assertEqual(
            [decl["name"] for decl in toolbox.TOOL_DECLS],
            [
                "record_expense",
                "record_income",
                "query_money",
                "create_bill",
                "create_installment",
                "list_commitments",
                "mark_paid",
            ],
        )
        today = toolbox.today_jst()
        bill = {
            "title": "家賃",
            "amount": 85000,
            "due_day": 27,
            "start_date": today.isoformat(),
            "category_code": "utility",
        }
        cases = [
            ("create_bill", [], "arguments must be an object"),
            ("create_bill", dict(bill, user_id=1), "unexpected argument: user_id"),
            ("create_bill", {k: v for k, v in bill.items() if k != "due_day"}, "missing argument: due_day"),
            ("create_bill", dict(bill, amount="85000"), "amount must be an integer"),
            ("create_bill", dict(bill, amount=0), "amount must be positive"),
            ("create_bill", dict(bill, amount=10000001), "amount is implausibly large"),
            ("create_bill", dict(bill, due_day=32), "due_day must be an integer from 1 to 31"),
            ("create_bill", dict(bill, start_date="2027/01/01"), "start_date must be YYYY-MM-DD"),
            ("create_bill", dict(bill, start_date="2027-02-30"), "start_date must be YYYY-MM-DD"),
            (
                "create_bill",
                dict(bill, start_date=date(today.year + 2, 1, 1).isoformat()),
                "start_date must be within 12 months of today",
            ),
            (
                "create_bill",
                dict(bill, category_code="rent"),
                "category_code must be a seeded expense category",
            ),
            (
                "create_installment",
                {
                    "title": "冷蔵庫",
                    "total_amount": 3,
                    "months": 6,
                    "due_day": 27,
                    "start_date": today.isoformat(),
                    "category_code": "daily",
                },
                "total_amount must be at least months",
            ),
            (
                "create_installment",
                {
                    "title": "冷蔵庫",
                    "total_amount": 100000,
                    "months": 25,
                    "due_day": 27,
                    "start_date": today.isoformat(),
                    "category_code": "daily",
                },
                "months must be an integer from 1 to 24",
            ),
            ("list_commitments", {"status": "pending"}, "status must be active, done, or canceled"),
            ("list_commitments", {"status": None}, "status must be active, done, or canceled"),
            ("mark_paid", {"commitment_id": 0}, "commitment_id must be an integer from 1 to 4294967295"),
            ("mark_paid", {"commitment_id": "1"}, "commitment_id must be an integer from 1 to 4294967295"),
        ]
        for name, args, expected in cases:
            with self.assertRaises(toolbox.ToolError) as caught:
                toolbox.validate(name, args)
            self.assertEqual(str(caught.exception), expected)
        self.assertEqual(toolbox.validate("list_commitments", {}), {"status": "active"})
        normalized = toolbox.validate("create_bill", bill)
        self.assertEqual((normalized["kind"], normalized["amount"]), ("bill", 85000))
        self.assertEqual(normalized["category"]["category_name"], "光熱費")


class CommitmentRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient

        from app.main import app
        from app.shared import auth

        cls.category_id = db.fetch_one(
            "SELECT category_id FROM categories WHERE kind = 'expense' AND code = 'other'"
        )["category_id"]
        cls.email = "cmt-route-" + uuid.uuid4().hex + "@example.invalid"
        cls.password = "commitment-pass-123"
        cls.user_id = db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
            ("route owner", cls.email, auth.hash_password(cls.password)),
        )
        cls.client = TestClient(app)
        token = csrf_value(cls.client.get("/login").text)
        cls.client.post(
            "/login", data={"email": cls.email, "password": cls.password, "csrf_token": token}
        )
        cls.token = csrf_value(cls.client.get("/commitments").text)

    @classmethod
    def tearDownClass(cls):
        db.execute("DELETE FROM chat_message WHERE user_id = %s", (cls.user_id,))
        db.execute("DELETE FROM transactions WHERE user_id = %s", (cls.user_id,))
        db.execute("DELETE FROM commitments WHERE user_id = %s", (cls.user_id,))
        db.execute("DELETE FROM users WHERE user_id = %s", (cls.user_id,))

    def make_due_bill(self, title):
        today = store.today_jst()
        with db.cursor(commit=True) as cur:
            return store.create_commitment(
                cur,
                self.user_id,
                {
                    "kind": "bill",
                    "title": title,
                    "amount": 85000,
                    "total_amount": None,
                    "months": None,
                    "due_day": today.day,
                    "start_date": today.replace(day=1),
                    "category_id": self.category_id,
                    "category_name": "その他",
                },
            )

    def test_anonymous_get_redirects_to_login(self):
        from fastapi.testclient import TestClient

        from app.main import app

        response = TestClient(app).get("/commitments", follow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["location"], "/login")

    def test_due_page_lists_row_and_escapes_title(self):
        bill = self.make_due_bill("<script>alert(1)</script>")
        page = self.client.get("/commitments")
        self.assertEqual(page.status_code, 200)
        self.assertIn("支払い予定", page.text)
        self.assertIn("毎月の支払い", page.text)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", page.text)
        self.assertNotIn("<script>alert(1)</script>", page.text)
        self.assertIn("¥85,000", page.text)
        self.assertIn(bill["next_due_date"].isoformat(), page.text)
        self.assertIn("支払った", page.text)
        self.assertIn('/commitments/{}/pay'.format(bill["id"]), page.text)

    def test_chat_page_renders_with_commitments_link(self):
        page = self.client.get("/chat")
        self.assertEqual(page.status_code, 200)
        self.assertIn('href="/commitments"', page.text)

    def test_pay_requires_csrf_and_a_fresh_snapshot(self):
        bill = self.make_due_bill("ルート確認 家賃")
        due = bill["next_due_date"].isoformat()
        url = "/commitments/{}/pay".format(bill["id"])
        no_csrf = self.client.post(
            url,
            data={"expected_due_date": due, "expected_last_txn_id": "0"},
            follow_redirects=False,
        )
        self.assertEqual(no_csrf.status_code, 403)
        stale = self.client.post(
            url,
            data={"csrf_token": self.token, "expected_due_date": "2000-01-01", "expected_last_txn_id": "0"},
            follow_redirects=False,
        )
        self.assertEqual(stale.status_code, 303)
        self.assertEqual(stale.headers["location"], "/commitments?error=stale")
        self.assertEqual(
            count_rows(
                "SELECT COUNT(*) AS n FROM transactions WHERE user_id = %s", (self.user_id,)
            ),
            0,
        )
        paid = self.client.post(
            url,
            data={"csrf_token": self.token, "expected_due_date": due, "expected_last_txn_id": "0"},
            follow_redirects=False,
        )
        self.assertEqual(paid.status_code, 303)
        linked = db.fetch_one(
            "SELECT txn_id FROM transactions WHERE user_id = %s AND commitment_id = %s",
            (self.user_id, bill["id"]),
        )
        self.assertIsNotNone(linked)
        self.assertEqual(paid.headers["location"], "/commitments?paid={}".format(linked["txn_id"]))
        row = db.fetch_one(
            "SELECT paid_count FROM commitments WHERE commitment_id = %s", (bill["id"],)
        )
        self.assertEqual(int(row["paid_count"]), 1)


class ChatCommitmentFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user_id = make_user("chat")
        cls.other_id = make_user("chatother")
        cls.category_id = db.fetch_one(
            "SELECT category_id FROM categories WHERE kind = 'expense' AND code = 'utility'"
        )["category_id"]

    @classmethod
    def tearDownClass(cls):
        for uid in (cls.user_id, cls.other_id):
            db.execute("DELETE FROM chat_message WHERE user_id = %s", (uid,))
            db.execute("DELETE FROM transactions WHERE user_id = %s", (uid,))
            db.execute("DELETE FROM commitments WHERE user_id = %s", (uid,))
            db.execute("DELETE FROM users WHERE user_id = %s", (uid,))
        left = count_rows(
            "SELECT (SELECT COUNT(*) FROM users WHERE user_id IN (%s, %s)) + "
            "(SELECT COUNT(*) FROM commitments WHERE user_id IN (%s, %s)) + "
            "(SELECT COUNT(*) FROM transactions WHERE user_id IN (%s, %s)) + "
            "(SELECT COUNT(*) FROM chat_message WHERE user_id IN (%s, %s)) AS n",
            (cls.user_id, cls.other_id) * 4,
        )
        if left:
            raise AssertionError("leftover fixture rows: " + str(left))

    def make_due_bill(self, user_id, title):
        today = store.today_jst()
        with db.cursor(commit=True) as cur:
            return store.create_commitment(
                cur,
                user_id,
                {
                    "kind": "bill",
                    "title": title,
                    "amount": 85000,
                    "total_amount": None,
                    "months": None,
                    "due_day": today.day,
                    "start_date": today.replace(day=1),
                    "category_id": self.category_id,
                    "category_name": "光熱費",
                },
            )

    def last_message(self, user_id):
        return db.fetch_one(
            "SELECT message_id FROM chat_message WHERE user_id = %s ORDER BY message_id DESC LIMIT 1",
            (user_id,),
        )["message_id"]

    def test_payment_proposal_writes_nothing_until_confirmed(self):
        bill = self.make_due_bill(self.user_id, "家賃チャット")
        self.assertEqual(service.propose_payment(self.user_id, {"commitment_id": bill["id"]})["type"], "proposal")
        self.assertEqual(
            count_rows(
                "SELECT COUNT(*) AS n FROM transactions WHERE user_id = %s", (self.user_id,)
            ),
            0,
        )
        message_id = self.last_message(self.user_id)
        row = db.fetch_one(
            "SELECT message_id, role, body, payload FROM chat_message WHERE message_id = %s",
            (message_id,),
        )
        row["payload"] = json.loads(row["payload"])
        self.assertEqual(row["payload"]["preview"]["amount"], 85000)
        self.assertIn("85000", json.dumps(row["payload"], ensure_ascii=False))
        from app.main import app

        env = app.state.templates.env
        card = env.get_template("_commitment_msg.html").render(m=row, csrf_token="t", categories=[])
        self.assertIn("支払った", card)
        self.assertIn("家賃チャット", card)
        self.assertIn("/chat/confirm/{}".format(message_id), card)
        saved = service.confirm(self.user_id, message_id, {})
        self.assertIsNotNone(saved)
        self.assertEqual(saved["commitment_id"], bill["id"])
        linked = db.fetch_one(
            "SELECT COUNT(*) AS n FROM transactions WHERE user_id = %s AND commitment_id = %s",
            (self.user_id, bill["id"]),
        )
        self.assertEqual(int(linked["n"]), 1)
        self.assertIsNone(service.confirm(self.user_id, message_id, {}))
        self.assertEqual(int(self.commitment_count(bill["id"])), 1)

    def test_invented_and_foreign_commitment_ids_are_refused(self):
        foreign = self.make_due_bill(self.other_id, "他人の水道代")
        before = count_rows(
            "SELECT COUNT(*) AS n FROM transactions WHERE user_id = %s", (self.user_id,)
        )
        self.assertEqual(service.propose_payment(self.user_id, {"commitment_id": 4294967295}), {"ok": False, "error": "not_found"})
        self.assertEqual(service.propose_payment(self.user_id, {"commitment_id": foreign["id"]}), {"ok": False, "error": "not_found"})
        after = count_rows(
            "SELECT COUNT(*) AS n FROM transactions WHERE user_id = %s", (self.user_id,)
        )
        self.assertEqual((before, after), (0, 0))

    def test_creation_proposal_creates_schedule_only_after_confirm(self):
        today = store.today_jst()
        raw = {
            "title": "冷蔵庫 チャット",
            "total_amount": 100000,
            "months": 6,
            "due_day": 27,
            "start_date": today.isoformat(),
            "category_code": "daily",
        }
        normalized = toolbox.validate("create_installment", raw)
        service.propose_creation(self.user_id, "create_installment", raw, normalized)
        self.assertEqual(
            count_rows(
                "SELECT COUNT(*) AS n FROM commitments WHERE user_id = %s AND title = %s",
                (self.user_id, "冷蔵庫 チャット"),
            ),
            0,
        )
        message_id = self.last_message(self.user_id)
        created = service.confirm(self.user_id, message_id, {"amount": "1", "date": "2020-01-01"})
        self.assertIsNotNone(created)
        row = db.fetch_one(
            "SELECT kind, amount, total_amount, months, paid_count, status FROM commitments "
            "WHERE user_id = %s AND title = %s",
            (self.user_id, "冷蔵庫 チャット"),
        )
        self.assertEqual(row["kind"], "installment")
        self.assertEqual((int(row["amount"]), int(row["total_amount"])), (16666, 100000))
        self.assertEqual((int(row["months"]), int(row["paid_count"])), (6, 0))
        self.assertEqual(row["status"], "active")
        self.assertEqual(
            count_rows(
                "SELECT COUNT(*) AS n FROM transactions WHERE user_id = %s", (self.user_id,)
            ),
            0,
        )

    def test_system_prompt_lists_active_commitments_only(self):
        self.make_due_bill(self.user_id, "プロンプト確認")
        self.make_due_bill(self.other_id, "他人のプロンプト")
        prompt = service.system_prompt(self.user_id)
        self.assertIn("プロンプト確認", prompt)
        self.assertNotIn("他人のプロンプト", prompt)

    def commitment_count(self, commitment_id):
        return count_rows(
            "SELECT COUNT(*) AS n FROM commitments WHERE commitment_id = %s", (commitment_id,)
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
