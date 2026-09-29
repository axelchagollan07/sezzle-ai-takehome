import json
import os
from pathlib import Path
from typing import Any


class OrdersRepository:
    """Read-only access layer for the synthetic Sezzle orders dataset."""

    def __init__(self, data_path: str | None = None) -> None:
        if data_path is None:
            data_dir = os.getenv("SEZZLE_DATA_DIR", "data")
            data_path = str(Path(data_dir) / "orders" / "DATA-orders.json")

        self.data_path = Path(data_path)

        if not self.data_path.exists():
            raise FileNotFoundError(
                f"Orders data file not found: {self.data_path}"
            )

        with self.data_path.open("r", encoding="utf-8") as file:
            self.data: dict[str, Any] = json.load(file)

        self.users = {
            user["user_id"]: user
            for user in self.data.get("users", [])
        }

        self.orders = {
            order["order_id"]: order
            for order in self.data.get("orders", [])
        }

    @property
    def today(self) -> str:
        """Return the frozen current date provided by the dataset."""
        return self.data["today"]

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        """Return a user by ID."""
        return self.users.get(user_id)

    def get_user_orders(self, user_id: str) -> list[dict[str, Any]]:
        """Return only orders belonging to the authenticated user."""
        return [
            order
            for order in self.orders.values()
            if order["user_id"] == user_id
        ]

    def get_order(
        self,
        user_id: str,
        order_id: str,
    ) -> dict[str, Any] | None:
        """
        Return an order only when it belongs to the requesting user.

        This authorization check intentionally lives outside the LLM.
        """
        order = self.orders.get(order_id)

        if order is None:
            return None

        if order["user_id"] != user_id:
            return None

        return order

    def get_order_for_user(
        self,
        user_id: str,
        order_id: str,
    ) -> dict[str, Any]:
        """
        Strict order lookup with explicit authorization outcomes.

        Raises:
            ValueError: if the order does not exist or belongs to another user.
        """
        order = self.orders.get(order_id)

        if order is None:
            raise ValueError("ORDER_NOT_FOUND")

        if order["user_id"] != user_id:
            raise ValueError("ORDER_NOT_AUTHORIZED")

        return order