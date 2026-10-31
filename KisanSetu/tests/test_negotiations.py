import unittest
import uuid

from app import app
from models import Crop, Negotiation, NegotiationChatMessage, Order, User, db


class NegotiationFlowTests(unittest.TestCase):
    def setUp(self):
        app.config["WTF_CSRF_ENABLED"] = False
        suffix = uuid.uuid4().hex

        with app.app_context():
            self.farmer = User(
                name="Test Farmer",
                email=f"farmer-{suffix}@example.test",
                role="farmer",
            )
            self.farmer.set_password("test-password")
            self.buyer = User(
                name="Test Buyer",
                email=f"buyer-{suffix}@example.test",
                role="buyer",
            )
            self.buyer.set_password("test-password")
            self.other_buyer = User(
                name="Other Buyer",
                email=f"other-{suffix}@example.test",
                role="buyer",
            )
            self.other_buyer.set_password("test-password")
            self.admin = User.query.filter_by(role="admin").first()
            db.session.add_all([self.farmer, self.buyer, self.other_buyer])
            db.session.flush()

            self.crop = Crop(
                farmer_id=self.farmer.id,
                name="Test Wheat",
                quantity=10,
                unit="kg",
                price_per_unit=60,
                status="active",
            )
            db.session.add(self.crop)
            db.session.commit()
            self.crop_id = self.crop.id
            self.farmer_id = self.farmer.id
            self.buyer_id = self.buyer.id
            self.other_buyer_id = self.other_buyer.id
            self.admin_id = self.admin.id

        self.buyer_client = app.test_client()
        self.farmer_client = app.test_client()
        self.other_buyer_client = app.test_client()
        self.admin_client = app.test_client()
        self._login(self.buyer_client, self.buyer_id)
        self._login(self.farmer_client, self.farmer_id)
        self._login(self.other_buyer_client, self.other_buyer_id)
        self._login(self.admin_client, self.admin_id)

        crop_page = self.buyer_client.get(f"/crops/{self.crop_id}")
        self.assertEqual(crop_page.status_code, 200)
        self.assertIn(b"Negotiate with the farmer", crop_page.data)

    @staticmethod
    def _login(client, user_id):
        with client.session_transaction() as session:
            session["_user_id"] = str(user_id)
            session["_fresh"] = True

    def tearDown(self):
        with app.app_context():
            negotiation_ids = [
                item.id for item in Negotiation.query.filter_by(
                    crop_id=self.crop_id
                ).all()
            ]
            for item in Negotiation.query.filter(
                Negotiation.id.in_(negotiation_ids)
            ).all():
                db.session.delete(item)
            Order.query.filter_by(crop_id=self.crop_id).delete()
            crop = db.session.get(Crop, self.crop_id)
            if crop:
                db.session.delete(crop)
            for user_id in (self.farmer_id, self.buyer_id, self.other_buyer_id):
                user = db.session.get(User, user_id)
                if user:
                    db.session.delete(user)
            db.session.commit()

    def test_offer_counter_and_accept_creates_agreed_order(self):
        response = self.buyer_client.post(
            f"/negotiations/new/{self.crop_id}",
            data={
                "quantity": "4",
                "offer_price": "50",
                "message": "Can collect this week",
            },
        )
        self.assertEqual(response.status_code, 302)

        with app.app_context():
            negotiation = Negotiation.query.filter_by(
                crop_id=self.crop_id,
                buyer_id=self.buyer_id,
            ).one()
            negotiation_id = negotiation.id

        page = self.farmer_client.get("/negotiations")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"Buyer-Seller Negotiation", page.data)
        self.assertIn(b"Can collect this week", page.data)

        response = self.farmer_client.post(
            f"/negotiations/{negotiation_id}/reply",
            data={"offer_price": "55", "message": "Freshly harvested"},
        )
        self.assertEqual(response.status_code, 302)

        response = self.buyer_client.post(
            f"/negotiations/{negotiation_id}/accept"
        )
        self.assertEqual(response.status_code, 302)

        page = self.buyer_client.get("/negotiations")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"Deal agreed", page.data)

        with app.app_context():
            negotiation = db.session.get(Negotiation, negotiation_id)
            crop = db.session.get(Crop, self.crop_id)
            order = db.session.get(Order, negotiation.order_id)
            self.assertEqual(negotiation.status, "accepted")
            self.assertEqual(negotiation.agreed_price, 55)
            self.assertEqual(len(negotiation.messages), 2)
            self.assertEqual(order.status, "accepted")
            self.assertEqual(order.price_per_unit, 55)
            self.assertEqual(order.total_amount, 220)
            self.assertEqual(crop.quantity, 6)

    def test_non_participant_cannot_reply_to_negotiation(self):
        self.buyer_client.post(
            f"/negotiations/new/{self.crop_id}",
            data={"quantity": "2", "offer_price": "50"},
        )
        with app.app_context():
            negotiation_id = Negotiation.query.filter_by(
                crop_id=self.crop_id
            ).one().id

        response = self.other_buyer_client.post(
            f"/negotiations/{negotiation_id}/reply",
            data={"offer_price": "52"},
        )
        self.assertEqual(response.status_code, 403)

    def test_offer_cannot_exceed_available_quantity(self):
        response = self.buyer_client.post(
            f"/negotiations/new/{self.crop_id}",
            data={"quantity": "11", "offer_price": "50"},
        )
        self.assertEqual(response.status_code, 302)
        with app.app_context():
            self.assertEqual(
                Negotiation.query.filter_by(crop_id=self.crop_id).count(),
                0,
            )

    def test_chat_messages_are_visible_to_parties_and_admin_read_only(self):
        self.buyer_client.post(
            f"/negotiations/new/{self.crop_id}",
            data={"quantity": "3", "offer_price": "52"},
        )
        with app.app_context():
            negotiation_id = Negotiation.query.filter_by(
                crop_id=self.crop_id
            ).one().id

        response = self.buyer_client.post(
            f"/negotiations/{negotiation_id}/messages",
            data={"message": "Can you share the harvest date?"},
        )
        self.assertEqual(response.status_code, 302)

        farmer_page = self.farmer_client.get("/negotiations")
        self.assertEqual(farmer_page.status_code, 200)
        self.assertIn(b"Can you share the harvest date?", farmer_page.data)

        admin_page = self.admin_client.get("/negotiations")
        self.assertEqual(admin_page.status_code, 200)
        self.assertIn(b"Marketplace conversations", admin_page.data)
        self.assertIn(b"Can you share the harvest date?", admin_page.data)
        self.assertNotIn(b"Write a message to", admin_page.data)

        response = self.admin_client.post(
            f"/negotiations/{negotiation_id}/messages",
            data={"message": "This should not be allowed"},
        )
        self.assertEqual(response.status_code, 403)

        response = self.other_buyer_client.post(
            f"/negotiations/{negotiation_id}/messages",
            data={"message": "Not a party"},
        )
        self.assertEqual(response.status_code, 403)

        with app.app_context():
            self.assertEqual(
                NegotiationChatMessage.query.filter_by(
                    negotiation_id=negotiation_id
                ).count(),
                1,
            )


if __name__ == "__main__":
    unittest.main()
