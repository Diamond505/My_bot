# MyBot

Local-only task manager and file organizer that runs on your PC.

## What it does
- Track tasks for multiple communities or projects (sim racing, DayZ, design work, server management).
- Organize files into folders based on simple extension rules.

## Quick start
```bash
python src/mybot.py add-task "Publish DayZ weekend event" --project "DayZ" --details "Post in Discord + update G-Portal"
python src/mybot.py list-tasks --status all
python src/mybot.py complete-task 1

# Preview file organization
python src/mybot.py organize --source ~/Downloads --dry-run

# Launch the desktop UI
python src/mybot.py gui
```

## File organization rules
Rules are stored in `data/rules.json`. Edit or extend them to match your workflow.

```json
{
  "rules": [
    {"name": "Images", "extensions": [".png", ".jpg"], "target": "Images"}
  ]
}
```

## Notes
- All data is stored locally in `data/`.
- This is a starting point. We can add reminders, recurring tasks, or a GUI if you want.
