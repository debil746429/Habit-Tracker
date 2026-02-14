# Habit Tracker

A command-line habit tracker built with Python. Track daily habits, log completions, and view streaks—all from your terminal.

## Features

- **Add habits** — Create new habits to track
- **View habits** — See today’s habits and their status
- **View streaks** — Check current and best streaks per habit
- **Log completion** — Mark habits as done (updates streaks automatically)
- **SQLite storage** — Data stored in `habit_tracker.db` (no extra setup)
- **Rich CLI** — Clear tables and formatting in the terminal

## Requirements

- Python 3.10+
- Dependencies in `requirements.txt`: `sqlalchemy`, `rich`, `rich-pyfiglet`

## Setup

```bash
# Clone or enter the project directory
git clone https://github.com/debil746429/Habit-Tracker.git
cd Habit-Tracker

# Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt
```

## Usage

Run the app:

```bash
python main.py
```

## Community & Contributions

- **Sample Video:**  
  [Watch a demo of Habit Tracker here](./Habit%20Tracker.mp4)

- **License:**  
  The project is licensed under the [MIT License](./LICENSE.md).

- **Contributing:**  
  Contributions are welcome! If you'd like to help improve, refactor, or extend this project, please open an issue or submit a pull request.

Join the community, grow together, and help make Habit Tracker even better!

