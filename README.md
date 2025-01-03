# AI-Powered Productivity Task Manager Bot

A Telegram bot that helps users manage tasks, set priorities, and get AI-powered productivity insights using the Deepseek API.

## Features

- 🎯 **Task Management**: Add, list, and complete tasks
- 🤖 **AI-Powered Analysis**: Automatic task analysis for priority and deadline suggestions
- 📊 **Smart Prioritization**: Get AI-recommended task prioritization
- ✅ **Progress Tracking**: Mark tasks as complete and get progress summaries
- 📝 **Natural Language Processing**: Chat naturally with the bot for productivity advice
- 🔄 **Context-Aware**: Bot maintains context of your tasks for better assistance

## Prerequisites

Before running the bot, make sure you have:

- Python 3.7+
- pip (Python package manager)
- Telegram account
- Telegram Bot Token (from @BotFather)
- Deepseek API Key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd productivity-bot
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your API keys:
```
TELEGRAM_TOKEN=your_telegram_bot_token_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

## Usage

1. Start the bot:
```bash
python bot.py
```

2. Open Telegram and search for @Producto124Bot

3. Start chatting with the bot using these commands:

- `/start` - Initialize the bot
- `/help` - View available commands
- `/add <task>` - Add a new task
- `/list` - View all tasks
- `/priority` - Get AI-based task prioritization
- `/complete <number>` - Mark a task as complete
- `/summary` - Get progress summary

## Example Usage

```
/add Complete project presentation by next Friday
```
The bot will:
- Add the task
- Analyze priority automatically
- Suggest deadline based on the description
- Break down into potential subtasks

## Features in Detail

### Task Analysis
- Automatically extracts priority levels (high/medium/low)
- Identifies deadlines from natural language
- Suggests logical subtasks

### AI Prioritization
- Uses context-aware AI to prioritize tasks
- Considers deadlines, dependencies, and importance
- Provides reasoning for prioritization decisions

### Progress Tracking
- Visual status indicators for tasks
- Progress summaries with AI insights
- Completion tracking and statistics

### Natural Language Interface
- Chat naturally about productivity
- Get personalized advice
- Context-aware responses based on your task list

## Error Handling

The bot includes comprehensive error handling for:
- Invalid commands
- API failures
- Network issues
- Invalid task numbers
- Missing permissions

## Technical Details

Built with:
- `python-telegram-bot` for Telegram integration
- Deepseek API for AI capabilities
- `python-dotenv` for environment management
- Async programming for better performance

## Security Notes

- API keys are stored in environment variables
- User data is stored in memory (non-persistent)
- Each user's tasks are isolated

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT License](LICENSE)

---

For more information or support, please open an issue in the repository.