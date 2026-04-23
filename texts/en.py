START_MESSAGE = """
🤖 <b>AI Access Bot v3.0</b>

🚀 Access to:
• ChatGPT-4o
• Claude 3.5 Sonnet
• Gemini 1.5 Pro
• Midjourney v6

🔹 49 ₽ forever
🔹 Enterprise API keys
🔹 Instant activation

Complete verification to get access.
"""

PAYMENT_INFO = """
🔐 <b>User Verification</b>

💰 Amount: {amount} ₽
💳 Card: <code>{card}</code>
🏦 Bank: {bank}

Click «I paid» after payment.

📌 <i>Why? Spam bot protection.</i>
"""

SUCCESS_ACTIVATION = """
✅ <b>Access Activated!</b>

🔑 Your key: <code>{api_key}</code>

⏳ Key activates in 10-15 minutes.

📌 Commands:
/key — show key
/support — help
"""

SUPPORT_MESSAGE = """
📞 <b>AI Access Bot Support</b>

🆔 Ticket number: <code>#{ticket_id}</code>

Describe your issue. Operator will respond within 24 hours.

Cancel: /cancel_support
"""

PROFILE_MESSAGE = """
👤 <b>Profile</b>

🆔 ID: <code>{user_id}</code>
📛 Name: {first_name}
📅 Joined: {joined_date}
💎 Status: {status}

🔑 API keys: {keys_count}
📊 Requests today: {requests_today}/{max_requests}
"""

REFERRAL_MESSAGE = """
🎁 <b>Referral Program</b>

🔗 Your link:
<code>{ref_link}</code>

📊 Invited: {total_refs}
💰 Paid: {paid_refs}
🎁 Bonuses: {bonus}

Invite friends and get bonuses!
"""

HELP_MESSAGE = """
📚 <b>Bot Help</b>

<b>Commands:</b>
/start — Main menu
/profile — Profile
/key — Show API key
/referral — Referral program
/support — Support
/trial — Activate trial (3 days)

<b>Questions?</b> Use /support
"""

TRIAL_ACTIVATED = """
✅ <b>Trial activated!</b>

📅 Duration: 3 days
🔑 Use /key to get test key
"""

NO_API_KEYS = """
❌ No active API keys

Complete verification or activate trial /trial
"""

KEY_INFO = """
🔑 <b>Your API key:</b>

<code>{key}</code>

⏳ Key activates in 10-15 minutes.
"""