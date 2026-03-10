"""
Telegram Adapter for Project Nikkei (PTB v20+ Async Implementation).
Implements ChatInterface via the python-telegram-bot library.
Bridged explicitly into the synchronous AgentZero orchestrator using asyncio to_thread.
"""
import asyncio
import logging
import uuid
import json
import html

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
        
        # State memory for interactive remote approvals
        self.pending_approvals = {}
        
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
            
            status = result.get('status', 'unknown')
            
            # Interactive Approval Interception
            if status == "pending_approval":
                action_id = str(uuid.uuid4())
                self.pending_approvals[action_id] = {
                    "tool": result.get("tool"),
                    "kwargs": result.get("kwargs", {})
                }
                
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Approve", callback_data=f"approve:{action_id}"),
                        InlineKeyboardButton("❌ Reject", callback_data=f"reject:{action_id}")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"⚠️ <b>{html.escape(str(result.get('message', 'Approval Required')))}</b>\n\n<pre>{html.escape(json.dumps(result.get('kwargs', {}), indent=2))}</pre>",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                return

            final_response = f"<b>Execution Matrix ({html.escape(status)})</b>\n\n"
            
            if 'manager_report' in result:
                # Assuming manager_report is plain text or we accept it as is (if it had markdown, it would render raw, but it's safer escaped)
                final_response += html.escape(str(result['manager_report']))
            elif 'result' in result:
                final_response += f"<pre>{html.escape(json.dumps(result['result'], indent=2))}</pre>"
            else:
                final_response += html.escape(str(result))
                
            await update.message.reply_text(final_response[:4000], parse_mode='HTML')
        except Exception as e:
            await update.message.reply_text(f"⚠️ <b>Router Fatal Exception</b>\n<pre>{html.escape(str(e))}</pre>", parse_mode='HTML')

    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Listens exclusively for [Approve/Reject] payload clicks from inline keyboards.
        """
        query = update.callback_query
        user_id = update.effective_user.id
        await query.answer()

        if not self._is_authorized_user(user_id):
            return

        data_parts = query.data.split(':')
        action = data_parts[0]
        action_id = data_parts[1] if len(data_parts) > 1 else None
        
        if action == "approve" and action_id in self.pending_approvals:
            payload = self.pending_approvals.pop(action_id)
            await query.edit_message_text(text="Action Approved ✅. Executing...")
            
            try:
                # Forcefully execute bypassing the RCE block
                result = await asyncio.to_thread(
                    self.agent.process_direct, payload["tool"], payload["kwargs"]
                )
                
                status = result.get('status', 'unknown')
                final_response = f"<b>Execution Matrix ({html.escape(status)})</b>\n\n"
                if 'result' in result:
                    final_response += f"<pre>{html.escape(json.dumps(result['result'], indent=2))}</pre>"
                else:
                    final_response += html.escape(str(result))
                    
                await query.message.reply_text(final_response[:4000], parse_mode='HTML')
                
            except Exception as e:
                await query.message.reply_text(f"⚠️ <b>Execution Failed</b>\n<pre>{html.escape(str(e))}</pre>", parse_mode='HTML')
                
        elif action == "reject" and action_id in self.pending_approvals:
            self.pending_approvals.pop(action_id)
            await query.edit_message_text(text="Action Rejected ❌.")
        else:
            await query.edit_message_text(text="⚠️ Action expired or invalid.")

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
        Legacy fallback if the Thread is not bridging context properly, 
        or if tests interact via CLI Mock modes. Since SecurityException pushes 
        state back up to the router, this method is fundamentally a local 
        safety wrapper now.
        """
        response = input(f"Terminal (Fallback) - Approve action? '{action_description}' [y/N]: ")
        return response.strip().lower() in ['y', 'yes', 'approve']
