import asyncio
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock, Mock

from aiogram import Dispatcher, types

from main import (
    BOT_COMMANDS,
    Settings,
    attach_proof,
    cancel_direct_topup_draft,
    create_dispatcher,
    create_direct_topup_request,
    create_order,
    get_direct_topup_draft,
    get_active_order,
    get_open_direct_topup,
    initialize_database,
    list_products,
    list_products_by_category,
    load_settings,
    pending_direct_topups,
    save_product,
    save_setting,
    get_setting,
    set_direct_topup_draft,
    SUPPORT_USERNAME,
    register_bot_commands,
    transition_direct_topup_request,
    transition_order,
)


class BotSettingsTests(unittest.TestCase):
    def test_missing_token_fails_with_setup_instructions(self) -> None:
        with self.assertRaisesRegex(ValueError, "TELEGRAM_BOT_TOKEN"):
            load_settings({"ADMIN_ID": "123456"})

    def test_malformed_token_is_not_echoed_in_error(self) -> None:
        bad_token = "not-a-valid-token"
        with self.assertRaises(ValueError) as raised:
            load_settings({"TELEGRAM_BOT_TOKEN": bad_token, "ADMIN_ID": "123456"})
        self.assertNotIn(bad_token, str(raised.exception))

    def test_missing_admin_id_fails_explicitly(self) -> None:
        token = f"123456789:{'A' * 35}"
        with self.assertRaisesRegex(ValueError, "ADMIN_ID"):
            load_settings({"TELEGRAM_BOT_TOKEN": token})

    def test_support_contact_uses_requested_username(self) -> None:
        self.assertEqual(SUPPORT_USERNAME, "@GUODA36")


class TelegramCommandTests(unittest.TestCase):
    def test_commands_are_registered_for_default_and_private_chats(self) -> None:
        bot = Mock()
        bot.set_my_commands = AsyncMock()

        asyncio.run(register_bot_commands(bot))

        calls = bot.set_my_commands.await_args_list
        self.assertEqual(len(calls), 2)
        self.assertEqual(
            [command.command for command in calls[0].kwargs["commands"]],
            ["start", "store", "products", "help"],
        )
        self.assertIsInstance(
            calls[0].kwargs["scope"], types.BotCommandScopeDefault
        )
        self.assertIsInstance(
            calls[1].kwargs["scope"], types.BotCommandScopeAllPrivateChats
        )


class OrderStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.sqlite3"
        initialize_database(self.database_path)
        save_product(
            self.database_path,
            "ff-100",
            "Free Fire 100 diamonds",
            Decimal("100"),
            "EGP",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_product_and_payment_instructions_persist(self) -> None:
        products = list_products(self.database_path)
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]["product_id"], "ff-100")

        save_setting(self.database_path, "payment_instructions", "Test instructions")
        self.assertEqual(
            get_setting(self.database_path, "payment_instructions"),
            "Test instructions",
        )

    def test_products_are_grouped_into_free_fire_and_pubg(self) -> None:
        save_product(
            self.database_path,
            "pubg-60",
            "PUBG Mobile 60 UC",
            Decimal("45"),
            "EGP",
        )

        free_fire = list_products_by_category(self.database_path, "ff")
        pubg = list_products_by_category(self.database_path, "pubg")
        self.assertEqual([product["product_id"] for product in free_fire], ["ff-100"])
        self.assertEqual([product["product_id"] for product in pubg], ["pubg-60"])

    def test_unknown_product_category_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown product category"):
            list_products_by_category(self.database_path, "unknown")

    def test_order_moves_through_review_and_delivery_states(self) -> None:
        order_id = create_order(self.database_path, 5678, "buyer", "ff-100")
        self.assertIsNotNone(order_id)
        self.assertIsNone(create_order(self.database_path, 5678, "buyer", "ff-100"))

        active = get_active_order(self.database_path, 5678)
        self.assertIsNotNone(active)
        proof = attach_proof(self.database_path, order_id, 5678, "telegram-file-id")
        self.assertIsNotNone(proof)

        self.assertIsNotNone(
            transition_order(
                self.database_path, order_id, "awaiting_review", "awaiting_code"
            )
        )
        self.assertIsNotNone(
            transition_order(
                self.database_path, order_id, "awaiting_code", "delivering"
            )
        )
        self.assertIsNotNone(
            transition_order(
                self.database_path, order_id, "delivering", "delivered"
            )
        )
        self.assertIsNone(get_active_order(self.database_path, 5678))

    def test_direct_topup_request_is_saved_and_can_be_completed(self) -> None:
        self.assertTrue(
            set_direct_topup_draft(
                self.database_path, 5678, "buyer", "ff"
            )
        )
        draft = get_direct_topup_draft(self.database_path, 5678)
        self.assertIsNotNone(draft)
        self.assertEqual(draft["game"], "ff")

        request = create_direct_topup_request(
            self.database_path, 5678, "123456789", "500 Diamonds"
        )
        self.assertIsNotNone(request)
        self.assertEqual(request["player_id"], "123456789")
        self.assertEqual(request["package_request"], "500 Diamonds")
        self.assertIsNone(get_direct_topup_draft(self.database_path, 5678))
        self.assertEqual(len(pending_direct_topups(self.database_path)), 1)

        self.assertFalse(
            set_direct_topup_draft(
                self.database_path, 5678, "buyer", "pubg"
            )
        )
        self.assertEqual(
            get_open_direct_topup(self.database_path, 5678)["id"],
            request["id"],
        )

        completed = transition_direct_topup_request(
            self.database_path,
            int(request["id"]),
            "awaiting_admin",
            "completed",
        )
        self.assertIsNotNone(completed)
        self.assertIsNone(get_open_direct_topup(self.database_path, 5678))
        self.assertEqual(pending_direct_topups(self.database_path), [])

    def test_direct_topup_draft_can_be_cancelled_and_bad_games_rejected(self) -> None:
        self.assertTrue(
            set_direct_topup_draft(
                self.database_path, 5678, "buyer", "pubg"
            )
        )
        self.assertTrue(cancel_direct_topup_draft(self.database_path, 5678))
        self.assertIsNone(get_direct_topup_draft(self.database_path, 5678))
        with self.assertRaisesRegex(ValueError, "Unknown top-up game"):
            set_direct_topup_draft(
                self.database_path, 5678, "buyer", "unknown"
            )

    def test_dispatcher_registers_handlers_without_network_access(self) -> None:
        settings = Settings(
            bot_token=f"123456789:{'A' * 35}",
            admin_id=123456,
            database_path=self.database_path,
        )
        dispatcher = create_dispatcher(settings)
        self.assertIsInstance(dispatcher, Dispatcher)
        self.assertGreater(len(dispatcher.message.handlers), 0)
        self.assertGreater(len(dispatcher.callback_query.handlers), 0)


if __name__ == "__main__":
    unittest.main()
