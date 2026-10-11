# Telegram Game-Code Store

A Python Aiogram bot for game-code orders with manual payment-review and administrator-controlled delivery. The repository also contains the shared pnpm workspace services.

## Run & Operate

- `python main.py` — run the Telegram bot using long polling
- `python -m unittest discover -s tests -v` — run the bot tests
- **Telegram Bot** workflow — run the bot persistently
- `pnpm --filter @workspace/api-server run dev` — run the API server (port 5000)
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- Required secret: `TELEGRAM_BOT_TOKEN` — Telegram bot token from BotFather
- Required env: `ADMIN_ID` — numeric Telegram account ID of the only administrator
- Required env for the shared API service: `DATABASE_URL` — Postgres connection string

## Stack

- Python 3.13, Aiogram 3
- pnpm workspaces, Node.js 24, TypeScript 5.9
- API: Express 5
- DB: PostgreSQL + Drizzle ORM
- Validation: Zod (`zod/v4`), `drizzle-zod`
- API codegen: Orval (from OpenAPI spec)
- Build: esbuild (CJS bundle)

## Where things live

- `main.py` — Aiogram handlers, SQLite order store, and polling entry point
- `tests/` — bot unit tests
- `data/` — local SQLite order database (ignored by Git)
- `artifacts/api-server/` — shared Express API
- `lib/` — shared workspace libraries

## Architecture decisions

- Telegram credentials are read from `TELEGRAM_BOT_TOKEN`; never commit the token to source control.
- The bot uses long polling and a local SQLite database; it does not require a public webhook URL.
- Payment instructions are configured by the admin in the bot; real codes are supplied only after an order is approved.

## Product

The bot supports manual Free Fire and PUBG code sales plus direct Player ID top-up requests. Code orders require a receipt review and real code supplied by the administrator; direct top-up requests collect a game, Player ID, and package, then go to the administrator for manual pricing, payment coordination, and fulfillment.

## User preferences

None recorded.

## Gotchas

- Keep the Telegram Bot workflow running for the bot to receive updates.
- Configure `ADMIN_ID`, at least one product, and payment instructions before accepting code orders. Direct top-up pricing and payment are coordinated manually by the administrator.
- Product IDs must begin with `ff-` for Free Fire or `pubg-` for PUBG; buyers browse both categories through `/products`.
- Direct top-up requests are saved separately from code orders. Buyers submit `Player ID | package` after choosing a game; the administrator confirms price/payment and marks the request complete only after doing the top-up.
- Admins can retrieve open direct requests with `/topups`. Telegram commands `/start`, `/store`, `/products`, and `/help` are registered at startup; `/help` directs customers to `@GUODA36`. The bot does not use a reply keyboard.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
