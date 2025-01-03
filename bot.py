import os
import json
from datetime import datetime
from typing import Dict, List, Optional

from openai import OpenAI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Task:
    def __init__(
        self,
        description: str,
        priority: Optional[str] = None,
        deadline: Optional[str] = None,
        status: str = "pending"
    ):
        self.description = description
        self.priority = priority or "medium"
        self.deadline = deadline
        self.status = status
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "description": self.description,
            "priority": self.priority,
            "deadline": str(self.deadline) if self.deadline else None,
            "status": self.status,
            "created_at": str(self.created_at)
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Task':
        task = cls(
            description=data["description"],
            priority=data.get("priority"),
            deadline=data.get("deadline"),
            status=data.get("status", "pending")
        )
        task.created_at = datetime.fromisoformat(data["created_at"])
        return task

class ProductivityBot:
    def __init__(self):
        # Load environment variables
        self.telegram_token = os.getenv('TELEGRAM_TOKEN')
        self.deepseek_key = os.getenv('DEEPSEEK_API_KEY')
        
        if not self.telegram_token or not self.deepseek_key:
            raise ValueError("Missing required environment variables. Please check .env file.")
        
        # Initialize Deepseek client
        self.client = OpenAI(
            api_key=self.deepseek_key,
            base_url="https://api.deepseek.com"
        )
        
        # User tasks storage: {user_id: [Task]}
        self.user_tasks: Dict[int, List[Task]] = {}
        
        # Initialize Telegram application
        self.application = Application.builder().token(self.telegram_token).build()
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup all command and message handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("add", self.add_task_command))
        self.application.add_handler(CommandHandler("list", self.list_tasks_command))
        self.application.add_handler(CommandHandler("priority", self.prioritize_tasks_command))
        self.application.add_handler(CommandHandler("complete", self.complete_task_command))
        self.application.add_handler(CommandHandler("summary", self.get_summary_command))
        
        # Callback and message handlers
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.handle_message
        ))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)

    async def get_ai_response(self, messages: List[Dict[str, str]]) -> str:
        """Get response from Deepseek API with context"""
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Deepseek API error: {str(e)}")
            return "Sorry, I encountered an error. Please try again later."

    async def analyze_task(self, task_description: str) -> Dict:
        """Analyze task using AI to extract priority, deadline, and subtasks"""
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a task analysis assistant. Extract task information "
                    "and return it in JSON format with the following structure: "
                    "{'priority': 'high/medium/low', 'deadline': 'YYYY-MM-DD or null', "
                    "'subtasks': ['subtask1', 'subtask2', ...]}"
                )
            },
            {
                "role": "user",
                "content": f"Analyze this task: {task_description}"
            }
        ]
        
        response = await self.get_ai_response(messages)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"priority": "medium", "deadline": None, "subtasks": []}

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /start is issued."""
        welcome_message = (
            "👋 Hello! I'm your AI Productivity Assistant.\n\n"
            "I can help you with:\n"
            "• Task management\n"
            "• Breaking down complex tasks\n"
            "• Setting reminders\n"
            "• Prioritizing work\n\n"
            "Use /help to see all available commands!"
        )
        await update.message.reply_text(welcome_message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /help is issued."""
        help_message = (
            "Available commands:\n\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/add <task> - Add a new task\n"
            "/list - Show all your tasks\n"
            "/priority - Get AI task prioritization\n"
            "/complete <number> - Mark a task as complete\n"
            "/summary - Get progress summary\n\n"
            "You can also just chat with me about:\n"
            "• Task management\n"
            "• Productivity advice\n"
            "• Time management\n"
            "• Breaking down projects"
        )
        await update.message.reply_text(help_message)

    async def add_task_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add a new task with AI analysis"""
        user_id = update.effective_user.id
        task_description = " ".join(context.args)
        
        if not task_description:
            await update.message.reply_text(
                "Please provide a task description: /add your task here"
            )
            return
            
        # Analyze task with AI
        analysis = await self.analyze_task(task_description)
        
        # Create and store task
        task = Task(
            description=task_description,
            priority=analysis.get("priority"),
            deadline=analysis.get("deadline")
        )
        
        if user_id not in self.user_tasks:
            self.user_tasks[user_id] = []
        self.user_tasks[user_id].append(task)
        
        # Create response message
        response = [
            f"✅ Task added: {task_description}",
            f"Priority: {task.priority}"
        ]
        
        if task.deadline:
            response.append(f"Deadline: {task.deadline}")
        
        if analysis.get("subtasks"):
            response.append("\nSuggested subtasks:")
            response.extend(f"• {subtask}" for subtask in analysis["subtasks"])
        
        await update.message.reply_text("\n".join(response))

    async def list_tasks_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all tasks with status and priority"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_tasks or not self.user_tasks[user_id]:
            await update.message.reply_text(
                "No tasks found. Add tasks using /add command."
            )
            return
        
        tasks = self.user_tasks[user_id]
        response = ["📋 Your Tasks:\n"]
        
        priority_emojis = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        status_emojis = {
            "completed": "✅",
            "in_progress": "🔄",
            "pending": "⏳"
        }
        
        for i, task in enumerate(tasks, 1):
            status_emoji = status_emojis.get(task.status, "⏳")
            priority_emoji = priority_emojis.get(task.priority, "🟡")
            
            task_line = f"{i}. {status_emoji} {priority_emoji} {task.description}"
            response.append(task_line)
            
            if task.deadline:
                response.append(f"   📅 Deadline: {task.deadline}")
            response.append("")  # Empty line between tasks
        
        await update.message.reply_text("\n".join(response))

    async def prioritize_tasks_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Use AI to reprioritize all tasks"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_tasks or not self.user_tasks[user_id]:
            await update.message.reply_text("No tasks to prioritize.")
            return
        
        tasks_info = [task.to_dict() for task in self.user_tasks[user_id]]
        
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a task prioritization assistant. Analyze tasks and "
                    "suggest priority order based on deadlines, importance, and dependencies."
                )
            },
            {
                "role": "user",
                "content": f"Prioritize these tasks and explain why: {json.dumps(tasks_info)}"
            }
        ]
        
        prioritized_response = await self.get_ai_response(messages)
        await update.message.reply_text(f"📊 Task Prioritization:\n\n{prioritized_response}")

    async def complete_task_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mark a task as completed"""
        user_id = update.effective_user.id
        
        if not context.args:
            await update.message.reply_text(
                "Please specify a task number: /complete <task_number>"
            )
            return
            
        try:
            task_index = int(context.args[0]) - 1
            task = self.user_tasks[user_id][task_index]
            task.status = "completed"
            await update.message.reply_text(
                f"✅ Task marked as completed: {task.description}"
            )
        except (IndexError, ValueError, KeyError):
            await update.message.reply_text(
                "Please specify a valid task number: /complete <task_number>"
            )

    async def get_summary_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get AI-generated summary of current tasks and progress"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_tasks or not self.user_tasks[user_id]:
            await update.message.reply_text("No tasks to summarize.")
            return
        
        tasks_info = [task.to_dict() for task in self.user_tasks[user_id]]
        
        messages = [
            {
                "role": "system",
                "content": "You are a productivity assistant. Provide a summary of tasks and progress."
            },
            {
                "role": "user",
                "content": f"Summarize the current task status and suggest next steps: {json.dumps(tasks_info)}"
            }
        ]
        
        summary = await self.get_ai_response(messages)
        await update.message.reply_text(f"📊 Progress Summary:\n\n{summary}")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages with AI context awareness"""
        user_id = update.effective_user.id
        user_message = update.message.text
        
        # Create context-aware prompt including user's tasks
        task_context = ""
        if user_id in self.user_tasks and self.user_tasks[user_id]:
            tasks_info = [task.to_dict() for task in self.user_tasks[user_id]]
            task_context = f"\nUser's current tasks: {json.dumps(tasks_info)}"
        
        messages = [
            {
                "role": "system",
                "content": (
                    f"You are a productivity assistant. Help the user with their tasks "
                    f"and productivity.{task_context}"
                )
            },
            {"role": "user", "content": user_message}
        ]
        
        response = await self.get_ai_response(messages)
        await update.message.reply_text(response)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards"""
        query = update.callback_query
        await query.answer()
        # Add callback handling logic here if needed

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors in the bot"""
        print(f"Error occurred: {context.error}")
        if update and isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "Sorry, an error occurred. Please try again later."
            )

    def run(self):
        """Run the bot."""
        print("Bot is starting...")
        self.application.run_polling()

if __name__ == '__main__':
    try:
        bot = ProductivityBot()
        bot.run()
    except Exception as e:
        print(f"Failed to start bot: {str(e)}")