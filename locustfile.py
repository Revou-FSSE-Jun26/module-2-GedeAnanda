import random

from locust import HttpUser, task, between


class ShopperUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.token = None
        self.product_ids = []

        email = f"loadtest_{random.randint(1, 1_000_000)}@test.com"
        response = self.client.post("/auth/register", json={
            "username": "loadtest",
            "email": email,
            "password": "password123"
        }, name="/auth/register")

        if response.status_code == 201:
            self.token = response.json()["data"]["access_token"]

    @property
    def headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    @task
    def shopping_journey(self):
        response = self.client.get("/products", name="/products")
        if response.status_code != 200:
            return

        products = response.json()["data"]
        if not products:
            return

        self.product_ids = [p["id"] for p in products if p["stock"] > 0]
        if not self.product_ids:
            return

        product_id = random.choice(self.product_ids)
        self.client.get(f"/products/{product_id}", name="/products/<id>")

        if not self.token:
            return

        order_response = self.client.post("/orders", json={
            "items": [{"product_id": product_id, "quantity": 1}]
        }, headers=self.headers, name="/orders")

        if order_response.status_code != 201:
            return

        order_id = order_response.json()["data"]["id"]
        self.client.get(f"/orders/{order_id}",
                        headers=self.headers,
                        name="/orders/<id>")