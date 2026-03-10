"""
Telegram Adapter for Project Nikkei (PTB v20+ Async Implementation).
Implements ChatInterface via the python-telegram-bot library.
Bridged explicitly into the synchronous AgentZero orchestrator using asyncio to_thread.
"""
import asyncio
import logging
import threading
from typing import Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters, ContextTypes

from adapters.chat.base import ChatInterface
from core.security import get_secret
import core.security


class TelegramAdapter(ChatInterface):
    """
    Telegram-specific implementation of the ChatInterface.
    Ensures that only an explicitly authorized ADMIN_CHAT_ID can interact.
    """
    def __init__(self, agent=None):
        from core.agent_zero import AgentZero
        self.agent = agent if agent else AgentZero()
        self.bot_token = get_secret("TELEGRAM_BOT_TOKEN")
        self.admin_chat_id = get_secret("TELEGRAM_ADMIN_CHAT_ID")
        
        self.application = None
        self._loop = None
        
        # Concurrency primitives for RCE Safeguards / Approvals
        self._approval_event = threading.Event()
        self._approval_result = False
        
        # Override the global fallback with our async interactive block
        core.security.require_interactive_approval = self.ask_for_approval

        if not self.bot_token or not self.admin_chat_id:
            logging.warning("Telegram credentials not found in keyring. Adapter might fail.")

    def _is_authorized_user(self, user_id: str | int) -> bool:
        """
        CRITICAL SECURITY REQUIREMENT: Identity Whitelist.
        Drops any incoming webhook/message where the user_id does not match admin ID.
        """
        return str(user_id) == str(self.admin_chat_id)

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Core message handler routing natural language securely to AgentZero.
        Runs PTB async handler, bridges to sync AgentZero, and awaits processing.
        """
        self._loop = asyncio.get_running_loop()
        user_id = update.effective_user.id
        
        if not self._is_authorized_user(user_id):
            logging.warning(f"Unauthorized access attempt from user_id: {user_id}")
            return
            
        print("[TelegramAdapter] Authorized message received. Processing in async bridge...")
        text = update.message.text
        
        # Bridge the synchronous processing of the agent into the async loop
        try:
            result = await asyncio.to_thread(self.agent.process_prompt, text)
            
            # Extract basic result fields to format nicely
            status = result.get('status', 'unknown')
            final_response = f"**Execution Matrix ({status})**\n\n"
            
            if 'manager_report' in result:
                final_response += result['manager_report']
            elif 'result' in result:
                import json
                final_response += f"```json\n{json.dumps(result['result'], indent=2)}\n```"
            else:
                final_response += str(result)
                
            await update.message.reply_text(final_response[:4000], parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"⚠️ **Router Fatal Exception**\n{e}")

    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Listens exclusively for [Approve/Reject] payload clicks from inline keyboards.
        """
        query = update.callback_query
        user_id = update.effective_user.id
        await query.answer()

        if not self._is_authorized_user(user_id):
            return

        print(f"[TelegramAdapter] RCE Callback Received: {query.data}")
        # Resolve the concurrency block
        self._approval_result = (query.data == "approve")
        self._approval_event.set()
        
        response_text = "Action Approved ✅" if self._approval_result else "Action Rejected ❌"
        await query.edit_message_text(text=response_text)

    def start_listening(self) -> None:
        """
        Bootstrap the ptb v20 Async Application engine in polling mode.
        """
        if not self.bot_token:
            return
            
        print("[TelegramAdapter] Initializing native Python-Telegram-Bot ApplicationBuilder...")
        self.application = ApplicationBuilder().token(self.bot_token).build()
        
        self.application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self._handle_message))
        self.application.add_handler(CallbackQueryHandler(self._handle_callback))
        
        print("[TelegramAdapter] Polling loop engaged. Awaiting directives.")
        self.application.run_polling()

    def send_message(self, text: str) -> None:
        """
        Synchronously bridges sending a text message out to the admin.
        """
        if self.application and self.application.bot and self._loop:
            asyncio.run_coroutine_threadsafe(
                self.application.bot.send_message(chat_id=self.admin_chat_id, text=text), 
                self._loop
            )
        else:
            print(f"[TelegramAdapter Error - Loop Offline] {text}")

    def ask_for_approval(self, action_description: str) -> bool:
        """
        Sends an inline keyboard [Approve] / [Reject] to the user asynchronously,
        but completely halts the yielding Thread execution loop until resolution.
        """
        print(f"[TelegramAdapter] RCE Safeguard Blocking Thread: {action_description}")
        
        self._approval_event.clear()
        self._approval_result = False
        
        if self._loop and self.application and self.application.bot:
            # Inject interactive elements into the active event loop
            keyboard = [
                [
                    InlineKeyboardButton("✅ Approve", callback_data="approve"),
                    InlineKeyboardButton("❌ Reject", callback_data="reject"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            asyncio.run_coroutine_threadsafe(
                self.application.bot.send_message(
                    chat_id=self.admin_chat_id,
                    text=f"⚠️ **RCE/Destructive Action Requested**\n\n```\n{action_description}\n```\nDo you want to proceed?",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                ),
                self._loop
            )
        else:
            # Fallback if loop died
            response = input(f"Telegram (Mock) - Approve action? '{action_description}' [y/N]: ")
            return response.strip().lower() in ['y', 'yes', 'approve']

        # Block the Tentacle thread execution exclusively until admin selects callback
        self._approval_event.wait(timeout=180) # 3 Min TTL
        
        return self._approval_result
