"""Faux TrustChange en mémoire : remplace les appels réseau du client pendant les tests."""
import json
import time

from app.billing import trustchange_client as tc

SECRET = "secret-de-test"


class FakeTrust:
    def __init__(self, monkeypatch):
        self.transactions: dict[str, dict] = {}
        self.unreachable = False
        monkeypatch.setattr(tc, "collect_mobile_money", self.collect)
        monkeypatch.setattr(tc, "get_transaction", self.get)

    async def collect(self, *, payment_code, phone_number, amount, external_reference, callback_url=None, metadata=None):
        if self.unreachable:
            raise tc.Unreachable("réseau coupé")
        if external_reference in self.transactions:
            raise tc.AlreadySubmitted("Référence déjà utilisée", 409)
        self.transactions[external_reference] = {
            "transactionId": f"TC-{len(self.transactions) + 1}", "externalReference": external_reference,
            "status": "PROCESSING", "amount": amount, "phoneNumber": tc.national_phone_number(phone_number)}
        return {"transactionId": self.transactions[external_reference]["transactionId"], "status": "PROCESSING"}

    async def get(self, reference):
        if reference not in self.transactions:
            raise tc.TrustChangeError("Transaction introuvable", 404)
        return self.transactions[reference]

    def finish(self, reference, status="SUCCESS", amount=None):
        self.transactions[reference]["status"] = status
        if amount is not None:
            self.transactions[reference]["amount"] = amount

    def webhook(self, reference, *, age=0, secret=SECRET):
        """Corps et en-têtes d'une notification signée pour cette transaction."""
        body = json.dumps({"data": self.transactions.get(reference, {"externalReference": reference})}).encode()
        ts = str(int(time.time()) - age)
        return body, {"X-TrustChange-Signature": tc.sign_webhook(body, ts, secret), "X-TrustChange-Timestamp": ts}
