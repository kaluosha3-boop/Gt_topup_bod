# Telegram Game Codes and Direct Top-Up Store

A Telegram bot built with Aiogram for Free Fire and PUBG game-code orders and manual Player ID top-up requests. Code buyers choose a configured product, receive payment instructions, send a receipt photo, and wait for an administrator to review it. Direct top-up buyers submit their game, Player ID, and requested package for the administrator to price and fulfill manually.

## Required configuration

- `TELEGRAM_BOT_TOKEN` — a protected Replit Secret containing the token from Telegram's BotFather.
- `ADMIN_ID` — the administrator's numeric Telegram account ID.

Never put the bot token, payment details, or game codes in source control. The bot stores its product catalog, payment instructions, and order statuses in an ignored local SQLite database at `data/telegram_bot.sqlite3`.

## Set up the store

1. Add `TELEGRAM_BOT_TOKEN` in Replit **Secrets**.
2. Set `ADMIN_ID` in the project environment.
3. Start the **Telegram Bot** workflow, then open a private chat with the bot.
4. Add products with `/addproduct <id> <price> <currency> <name>`. Use IDs beginning with `ff-` for Free Fire and `pubg-` for PUBG:

   ```text
   /addproduct ff-100 100 EGP Free Fire 100 diamonds
   /addproduct pubg-60 45 EGP PUBG Mobile 60 UC
   ```

5. Set the payment instructions shown to buyers:

   ```text
   /setpayment <your transfer instructions>
   ```

## Store flow

- `/store` opens the service menu. `/products` goes directly to the Free Fire and PUBG code catalog.
- Code buyers choose a product, follow the configured payment instructions, and send a receipt photo. The product list has buttons to return to categories and the service menu.
- Direct top-up buyers choose Free Fire or PUBG and send the Player ID and requested package in one message, formatted as `123456789 | 500 Diamonds`. The bot saves the request and sends it to the administrator.
- Direct top-ups are manual: the administrator confirms price and payment with the customer, performs the top-up, then marks the request completed or rejects it. The bot does not claim a top-up happened automatically.
- The administrator can retrieve open direct requests with `/topups`; each request includes buttons to mark it completed or reject it.
- Telegram's command menu is registered on startup with `/start`, `/store`, `/products`, and `/help`. `/help` sends customers directly to `@GUODA36`. The bot does not use a reply keyboard.
- The administrator receives the receipt with approve/reject buttons. Only the configured administrator can use them.
- After approval, the administrator sends the actual code with `/deliver <order_id> <real code>`.
- The bot does not pretend to verify a transfer or generate game codes. An administrator must review payment and supply the real code.
- Buyers can use `/cancel` to cancel an order only before sending a receipt.

The bot uses long polling, so its workflow must remain running. It does not require a public webhook URL.

## Run and test

```sh
python main.py
python -m unittest discover -s tests -v
```
