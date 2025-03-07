"""
This module contains unit tests for the `Pizza` model and API endpoints.

The tests cover the following functionalities:
- API endpoints

"""

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from insalan.pizza.models import Pizza, TimeSlot, Order, PizzaOrder, PizzaExport
from insalan.user.models import User


class PizzaEndpointsTestCase(TestCase):
    """Test the pizza model"""

    def setUp(self):
        self.admin_user = User.objects.create(
            username="admin", email="admin@example.com", is_staff=True
        )

        self.pizza1 = Pizza.objects.create(name="Test Pizza")
        self.pizza2 = Pizza.objects.create(name="Test Pizza 2")

        self.time_slot = TimeSlot.objects.create(
            start=timezone.now(),
            end=timezone.now() + timedelta(hours=1),
            delivery_time=timezone.now() + timedelta(hours=2),
            pizza_max=100,
            player_price=10,
            staff_price=5,
            external_price=15,
        )

        self.order = Order.objects.create(
            time_slot=self.time_slot, user="Test user", price=10
        )
        self.orderpizza1 = PizzaOrder.objects.create(
            order=self.order, pizza=self.pizza1
        )
        self.orderpizza2 = PizzaOrder.objects.create(
            order=self.order, pizza=self.pizza2
        )

    def test_pizza_list(self):
        """Test the pizza list endpoint"""
        client = APIClient()
        response = client.get(reverse("pizza/list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0], self.pizza1.id)
        self.assertEqual(response.data[1], self.pizza2.id)

    def test_pizza_post(self):
        """Test the pizza post endpoint"""
        client = APIClient()
        client.force_login(user=self.admin_user)
        response = client.post(reverse("pizza/list"), {"name": "Test Pizza 3"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Test Pizza 3")
        self.assertEqual(Pizza.objects.count(), 3)

    def test_pizza_post_unauthorized(self):
        """Test the pizza post endpoint with unauthorized user"""
        client = APIClient()
        response = client.post(reverse("pizza/list"), {"name": "Test Pizza 3"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Pizza.objects.count(), 2)

    def test_pizza_list_full(self):
        """Test the pizza list full endpoint"""
        client = APIClient()
        response = client.get(reverse("pizza/list/full"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["name"], "Test Pizza")
        self.assertEqual(response.data[1]["name"], "Test Pizza 2")

    def test_pizza_detail(self):
        """Test the pizza detail endpoint"""
        client = APIClient()
        response = client.get(reverse("pizza/detail", kwargs={"pk": self.pizza1.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Test Pizza")

    def test_pizza_detail_not_found(self):
        """Test the pizza detail endpoint with wrong id"""
        client = APIClient()
        response = client.get(reverse("pizza/detail", kwargs={"pk": 999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_pizza_search(self):
        """Test the pizza search endpoint"""
        client = APIClient()
        response = client.get(reverse("pizza/fuzzy-find"), {"q": "2"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Test Pizza 2")

    def test_pizza_by_timeslot(self):
        """Test the pizza by timeslot endpoint"""
        client = APIClient()
        client.force_login(user=self.admin_user)
        response = client.get(reverse("pizza/list/by-timeslot"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.time_slot.id)

    def test_pizza_by_timeslot_unauthorized(self):
        """Test the pizza by timeslot endpoint with unauthorized user"""
        client = APIClient()
        response = client.get(reverse("pizza/list/by-timeslot"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_pizza_by_timeslot_id(self):
        """Test the pizza by timeslot id endpoint"""
        client = APIClient()
        response = client.get(
            reverse("pizza/list/by-timeslot-id", kwargs={"pk": self.time_slot.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["pizza"]), 2)
        self.assertEqual(response.data["pizza"][self.pizza1.id], 1)
        self.assertEqual(response.data["pizza"][self.pizza2.id], 1)

    def test_pizza_by_timeslot_id_not_found(self):
        """Test the pizza by timeslot id endpoint with wrong id"""
        client = APIClient()
        response = client.get(
            reverse("pizza/list/by-timeslot-id", kwargs={"pk": 999})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_pizza_put(self) -> None:
        """Test the pizza put endpoint"""
        client = APIClient()
        client.force_login(user=self.admin_user)
        pizza_id: int = self.pizza1.id
        response = client.put(reverse(
            "pizza/detail",
            kwargs={"pk": pizza_id}
        ), {"name": "New Pizza Name"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            "id": pizza_id,
            "name": "New Pizza Name",
            "ingredients": None,
            "allergens": None,
            "image": None
        })

    def test_pizza_put_unauthorized(self) -> None:
        """Test the pizza put endpoint with unauthorized user"""
        client = APIClient()
        pizza_id: int = self.pizza1.id
        response = client.put(reverse(
            "pizza/detail",
            kwargs={"pk": pizza_id}
        ), {"name": "New Pizza Name"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {
            "detail": "Informations d'authentification non fournies."
        })
        self.assertEqual(Pizza.objects.get(id=pizza_id).name, "Test Pizza")

    def test_pizza_put_not_found(self) -> None:
        "Test the pizza put endpoint with wrong id"""
        client = APIClient()
        client.force_login(user=self.admin_user)
        response = client.put(reverse(
            "pizza/detail",
            kwargs={"pk": 999}
        ), {"name": "New Pizza Name"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {
            "detail": "Pas trouvé."
        })

    def test_pizza_patch(self) -> None:
        """Test the pizza patch endpoint"""
        client = APIClient()
        client.force_login(user=self.admin_user)
        pizza_id: int = self.pizza1.id
        response = client.patch(reverse(
            "pizza/detail",
            kwargs={"pk": pizza_id}
        ), {"name": "New Pizza Name"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            "id": pizza_id,
            "name": "New Pizza Name",
            "ingredients": None,
            "allergens": None,
            "image": None
        })

    def test_pizza_patch_unauthorized(self) -> None:
        """Test the pizza patch endpoint with unauthorized user"""
        client = APIClient()
        pizza_id: int = self.pizza1.id
        response = client.patch(reverse(
            "pizza/detail",
            kwargs={"pk": pizza_id}
        ), {"name": "New Pizza Name"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {
            "detail": "Informations d'authentification non fournies."
        })
        self.assertEqual(Pizza.objects.get(id=pizza_id).name, "Test Pizza")

    def test_pizza_patch_not_found(self) -> None:
        "Test the pizza patch endpoint with wrong id"""
        client = APIClient()
        client.force_login(user=self.admin_user)
        response = client.patch(reverse(
            "pizza/detail",
            kwargs={"pk": 999}
        ), {"name": "New Pizza Name"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {
            "detail": "Pas trouvé."
        })

    def test_pizza_delete(self) -> None:
        """Test the pizza delete endpoint"""
        client = APIClient()
        client.force_login(user=self.admin_user)
        response = client.delete(
            reverse("pizza/detail", kwargs={"pk": self.pizza1.id})
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Pizza.objects.count(), 1)

    def test_pizza_delete_unauthorized(self) -> None:
        """Test the pizza delete endpoint with unauthorized user"""
        client = APIClient()
        response = client.delete(
            reverse("pizza/detail", kwargs={"pk": self.pizza1.id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Pizza.objects.count(), 2)

    def test_pizza_delete_not_found(self) -> None:
        """Test the pizza delete endpoint with wrong id"""
        client = APIClient()
        client.force_login(user=self.admin_user)
        response = client.delete(
            reverse("pizza/detail", kwargs={"pk": 999})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Pizza.objects.count(), 2)

    def test_timeslot_list(self):
        """Test the timeslot list endpoint"""
        client = APIClient()
        response = client.get(reverse("timeslot/list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0], self.time_slot.id)

    def test_timeslot_post(self):
        """Test the timeslot post endpoint"""
        client = APIClient()
        client.force_login(user=self.admin_user)
        response = client.post(
            reverse("timeslot/list"),
            {
                "start": timezone.now(),
                "end": timezone.now() + timedelta(hours=1),
                "delivery_time": timezone.now() + timedelta(hours=2),
                "pizza_max": 100,
                "player_price": 10,
                "staff_price": 5,
                "external_price": 15,
                "pizza": [self.pizza1.id],
                "public": True,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["pizza_max"], 100)
        self.assertEqual(TimeSlot.objects.count(), 2)

    def test_timeslot_post_unauthorized(self):
        """Test the timeslot post endpoint with unauthorized user"""
        client = APIClient()
        response = client.post(
            reverse("timeslot/list"),
            {
                "start": timezone.now(),
                "end": timezone.now() + timedelta(hours=1),
                "delivery_time": timezone.now() + timedelta(hours=2),
                "pizza_max": 100,
                "player_price": 10,
                "staff_price": 5,
                "external_price": 15,
                "pizza": [self.pizza1.id],
                "public": True,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(TimeSlot.objects.count(), 1)

    def test_timeslot_list_full(self):
        """Test the timeslot list full endpoint"""
        client = APIClient()
        response = client.get(reverse("timeslot/list/full"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.time_slot.id)

    def test_timeslot_detail(self):
        """Test the timeslot detail endpoint"""
        client = APIClient()
        client.force_login(user=self.admin_user)
        response = client.get(
            reverse("timeslot/detail", kwargs={"pk": self.time_slot.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.time_slot.id)

    def test_timeslot_detail_unauthorized(self):
        """Test the timeslot detail endpoint with unauthorized user"""
        client = APIClient()
        response = client.get(
            reverse("timeslot/detail", kwargs={"pk": self.time_slot.id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_timeslot_delete(self):
        """Test the timeslot delete endpoint"""
        client = APIClient()
        client.force_login(user=self.admin_user)
        response = client.delete(
            reverse("timeslot/detail", kwargs={"pk": self.time_slot.id})
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TimeSlot.objects.count(), 0)

    def test_timeslot_delete_unauthorized(self):
        """Test the timeslot delete endpoint with unauthorized user"""
        client = APIClient()
        response = client.delete(
            reverse("timeslot/detail", kwargs={"pk": self.time_slot.id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(TimeSlot.objects.count(), 1)

    def test_timeslot_detail_not_found(self):
        """Test the timeslot detail endpoint with wrong id"""
        client = APIClient()
        client.force_login(user=self.admin_user)
        response = client.get(reverse("timeslot/detail", kwargs={"pk": 999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_timeslot_next(self):
        """Test the timeslot next endpoint"""
        client = APIClient()
        response = client.get(reverse("timeslot/list/next"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], self.time_slot.id)

    def test_order_list(self):
        """Test the order list endpoint"""
        client = APIClient()
        client.force_login(user=self.admin_user)
        response = client.get(reverse("order/list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0], self.order.id)

    def test_order_list_unauthorized(self):
        """Test the order list endpoint with unauthorized user"""
        client = APIClient()
        response = client.get(reverse("order/list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_order_post(self):
        """Test the order post endpoint"""
        client = APIClient()
        client.force_login(user=self.admin_user)
        response = client.post(
            reverse("order/list"),
            {
                "time_slot": self.time_slot.id,
                "pizza": [self.pizza1.id],
                'type': 'staff',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["time_slot"], self.time_slot.id)
        self.assertEqual(response.data["pizza"][0], self.pizza1.id)
        self.assertEqual(response.data["price"], 5)
        self.assertEqual(Order.objects.count(), 2)

    def test_order_external_price_post(self):
        """Test the order post endpoint"""
        client = APIClient()
        client.force_login(user=self.admin_user)
        response = client.post(
            reverse("order/list"),
            {
                "time_slot": self.time_slot.id,
                "pizza": [self.pizza1.id],
                'type': 'external',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["time_slot"], self.time_slot.id)
        self.assertEqual(response.data["pizza"][0], self.pizza1.id)
        self.assertEqual(response.data["price"], 15)
        self.assertEqual(Order.objects.count(), 2)

    def test_order_post_unauthorized(self):
        """Test the order post endpoint with unauthorized user"""
        client = APIClient()
        response = client.post(
            reverse("order/list"),
            {"time_slot": self.time_slot.id, "pizza": [self.pizza1.id]},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Order.objects.count(), 1)

    def test_order_post_not_found(self):
        """Test the order post endpoint with wrong id"""
        client = APIClient()
        client.force_login(user=self.admin_user)
        response = client.post(
            reverse("order/list"), {"time_slot": 999, "pizza": [self.pizza1.id]}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 1)

    def test_order_post_twice(self) -> None:
        """Test send to the order post endpoint an order twice"""
        client = APIClient()
        client.force_login(user=self.admin_user)
        response = client.post(
            reverse("order/list"),
            {
                "user": "user1",
                "time_slot": self.time_slot.id,
                "pizza": [self.pizza1.id],
                'type': 'staff',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order_id: int = response.data["id"]
        self.assertEqual(Order.objects.count(), 2)
        response = client.post(
            reverse("order/list"),
            {
                "user": "user1",
                "time_slot": self.time_slot.id,
                "pizza": [self.pizza1.id],
                'type': 'staff',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 2)
        response = client.post(
            reverse("order/list"),
            {
                "user": "user1",
                "time_slot": self.time_slot.id,
                "pizza": [self.pizza2.id],
                'type': 'staff',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 3)
        response = client.post(
            reverse("order/list"),
            {
                "user": "user2",
                "time_slot": self.time_slot.id,
                "pizza": [self.pizza1.id],
                'type': 'staff',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 4)
        order = Order.objects.get(pk=order_id)
        order.created_at = timezone.now() - timedelta(minutes=30)
        order.save()
        response = client.post(
            reverse("order/list"),
            {
                "user": "user1",
                "time_slot": self.time_slot.id,
                "pizza": [self.pizza1.id],
                'type': 'staff',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 5)

    def test_order_list_full(self):
        """Test the order list full endpoint"""
        client = APIClient()
        client.force_login(user=self.admin_user)
        response = client.get(reverse("order/list/full"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.order.id)

    def test_order_list_full_unauthorized(self):
        """Test the order list endpoint with unauthorized user"""
        client = APIClient()
        response = client.get(reverse("order/list/full"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_order_detail(self):
        """Test the order detail endpoint"""
        client = APIClient()
        client.force_login(user=self.admin_user)
        response = client.get(reverse("order/detail", kwargs={"pk": self.order.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.order.id)

    def test_order_detail_unauthorized(self):
        """Test the order detail endpoint with unauthorized user"""
        client = APIClient()
        response = client.get(reverse("order/detail", kwargs={"pk": self.order.id}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_order_detail_not_found(self):
        """Test the order detail endpoint with wrong id"""
        client = APIClient()
        client.force_login(user=self.admin_user)
        response = client.get(reverse("order/detail", kwargs={"pk": 999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_order_patch(self):
        """Test the order patch endpoint"""
        client = APIClient()
        client.force_login(user=self.admin_user)
        response = client.patch(
            reverse("order/detail", kwargs={"pk": self.order.id}),
            {"delivered": True},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"detail": "Modified."})

    def test_order_patch_unauthorized(self):
        """Test the order patch endpoint with unauthorized user"""
        client = APIClient()
        response = client.patch(
            reverse("order/detail", kwargs={"pk": self.order.id}),
            {"delivered": True},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_order_patch_not_found(self):
        """Test the order patch endpoint with wrong id"""
        client = APIClient()
        client.force_login(user=self.admin_user)
        response = client.patch(
            reverse("order/detail", kwargs={"pk": 999}), {"delivered": True}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_order_delete(self):
        """Test the order delete endpoint"""
        client = APIClient()
        client.force_login(user=self.admin_user)
        response = client.delete(
            reverse("order/detail", kwargs={"pk": self.order.id})
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Order.objects.count(), 0)

    def test_order_delete_unauthorized(self):
        """Test the order delete endpoint with unauthorized user"""
        client = APIClient()
        response = client.delete(
            reverse("order/detail", kwargs={"pk": self.order.id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Order.objects.count(), 1)

    def test_order_delete_not_found(self):
        """Test the order delete endpoint with wrong id"""
        client = APIClient()
        client.force_login(user=self.admin_user)
        response = client.delete(
            reverse("order/detail", kwargs={"pk": 999})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Order.objects.count(), 1)

    def test_export_order_unauthorized(self):
        """Test the export order endpoint with unauthorized user"""
        client = APIClient()
        response = client.get(
            reverse("timeslot/export", kwargs={"pk": self.time_slot.id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_export_order_not_found(self):
        """Test the export order endpoint with wrong id"""
        client = APIClient()
        client.force_login(user=self.admin_user)
        response = client.get(
            reverse("timeslot/export", kwargs={"pk": 999})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_export_order_empty(self):
        """Test the export order endpoint"""
        client = APIClient()
        client.force_login(user=self.admin_user)
        response = client.get(
            reverse("timeslot/export", kwargs={"pk": self.time_slot.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_export_order(self):
        """Test the export order endpoint"""
        client = APIClient()
        client.force_login(user=self.admin_user)

        export = PizzaExport.objects.create(time_slot=self.time_slot)
        export.orders.add(self.order)

        response = client.get(
            reverse("timeslot/export", kwargs={"pk": self.time_slot.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], export.id)
        self.assertEqual(response.data[0]["orders"][self.order.pizza.all()[0].name], 1)
        self.assertEqual(response.data[0]["orders"][self.order.pizza.all()[1].name], 1)

    def test_export_order_post(self):
        """Test the export order post endpoint"""
        client = APIClient()
        client.force_login(user=self.admin_user)
        response = client.post(
            reverse("timeslot/export", kwargs={"pk": self.time_slot.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["orders"][self.order.pizza.all()[0].name], 1)
        self.assertEqual(response.data[0]["orders"][self.order.pizza.all()[1].name], 1)

    def test_export_order_post_full(self):
        """Test the export order post endpoint"""
        client = APIClient()
        client.force_login(user=self.admin_user)

        export = PizzaExport.objects.create(time_slot=self.time_slot)
        export.orders.add(self.order)

        response = client.post(
            reverse("timeslot/export", kwargs={"pk": self.time_slot.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["orders"][self.order.pizza.all()[0].name], 1)

class TestExportOrderGet(TestCase):
    """Test the export get view."""

    def setUp(self) -> None:
        self.admin_user = User.objects.create(
            username="admin", email="admin@example.com", is_staff=True
        )

        self.time_slot = TimeSlot.objects.create(
            start=timezone.now(),
            end=timezone.now() + timedelta(hours=1),
            delivery_time=timezone.now() + timedelta(hours=2),
            pizza_max=100,
            player_price=10,
            staff_price=5,
            external_price=15,
        )

        self.export = PizzaExport.objects.create(time_slot=self.time_slot)
        
    def test_export_get(self) -> None:
        """Test the export get endpoint."""
        client = APIClient()
        client.force_login(user=self.admin_user)
        response = client.get(
            reverse("export/detail", kwargs={"pk": self.export.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.export.id)
        
    def test_export_get_unauthorized(self) -> None:
        """Test the export get endpoint with unauthorized user."""
        client = APIClient()
        response = client.get(
            reverse("export/detail", kwargs={"pk": self.export.id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_export_get_not_found(self) -> None:
        """Test the export get endpoint with wrong id."""
        client = APIClient()
        client.force_login(user=self.admin_user)
        response = client.get(
            reverse("export/detail", kwargs={"pk": 999})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class TestExportOrderDelete(TestCase):
    """Test the export delete view."""

    def setUp(self) -> None:
        self.admin_user = User.objects.create(
            username="admin", email="admin@example.com", is_staff=True
        )

        self.time_slot = TimeSlot.objects.create(
            start=timezone.now(),
            end=timezone.now() + timedelta(hours=1),
            delivery_time=timezone.now() + timedelta(hours=2),
            pizza_max=100,
            player_price=10,
            staff_price=5,
            external_price=15,
        )

        self.export = PizzaExport.objects.create(time_slot=self.time_slot)

    def test_export_delete(self) -> None:
        """Test the export delete endpoint."""
        client = APIClient()
        client.force_login(user=self.admin_user)
        response = client.delete(
            reverse("export/detail", kwargs={"pk": self.export.id})
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(PizzaExport.objects.count(), 0)

    def test_export_delete_unauthorized(self) -> None:
        """Test the export delete endpoint with unauthorized user."""
        client = APIClient()
        response = client.delete(
            reverse("export/detail", kwargs={"pk": self.export.id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(PizzaExport.objects.count(), 1)

    def test_pizza_delete_not_found(self) -> None:
        """Test the export delete endpoint with wrong id."""
        client = APIClient()
        client.force_login(user=self.admin_user)
        response = client.delete(
            reverse("pizza/detail", kwargs={"pk": 999})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(PizzaExport.objects.count(), 1)
