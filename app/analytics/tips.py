from __future__ import annotations

from typing import Any


def generate_daily_tips(payload: dict[str, Any]) -> list[dict[str, str]]:
    tips: list[dict[str, str]] = []

    openings = payload.get("openings")
    if isinstance(openings, dict):
        worst_openings = openings.get("worst")
        if isinstance(worst_openings, list) and worst_openings:
            first = worst_openings[0]
            if isinstance(first, dict):
                opening_name = str(first.get("opening") or "this opening")
                winrate = first.get("winrate")
                tips.append(
                    {
                        "icon": "📘",
                        "title": "Patch Your Weakest Opening",
                        "body": f"{opening_name} is your weakest line ({winrate}% winrate). Review 2 model games and one trap-free setup.",
                        "priority": "high",
                    }
                )

    tilt = payload.get("tilt")
    if isinstance(tilt, dict):
        level = str(tilt.get("level") or "LOW").upper()
        if level == "HIGH":
            tips.append(
                {
                    "icon": "🛑",
                    "title": "Tilt Cooldown First",
                    "body": "Your tilt level is HIGH. Pause for 10 minutes, breathe, then return with a strict 1-game focus.",
                    "priority": "high",
                }
            )
        elif level == "MEDIUM":
            tips.append(
                {
                    "icon": "🧘",
                    "title": "Mindfulness Reset",
                    "body": "Tilt is MEDIUM. Before queueing, do a short reset: stand up, breathe deeply, and define one calm objective.",
                    "priority": "medium",
                }
            )

    time_management = payload.get("time_management")
    if isinstance(time_management, dict):
        panic_ratio = time_management.get("panic_move_ratio")
        if isinstance(panic_ratio, (int, float)) and panic_ratio > 30:
            tips.append(
                {
                    "icon": "⏱️",
                    "title": "Reduce Panic Moves",
                    "body": f"Panic move ratio is {round(float(panic_ratio), 2)}%. Force a 3-second blunder check before every move.",
                    "priority": "high",
                }
            )

    weaknesses = payload.get("weaknesses")
    if isinstance(weaknesses, dict):
        items = weaknesses.get("items")
        if isinstance(items, list):
            for item in items:
                if not isinstance(item, dict):
                    continue
                label = str(item.get("label") or "")
                severity = str(item.get("severity") or "").upper()
                if label == "Endgame Conversion" and severity == "HIGH":
                    tips.append(
                        {
                            "icon": "♟️",
                            "title": "Endgame Focus Block",
                            "body": "Endgame conversion is a high-severity weakness. Study one king+pawn and one rook endgame pattern today.",
                            "priority": "high",
                        }
                    )
                    break

    generic_pool = [
        {
            "icon": "🧩",
            "title": "Play Fewer, Better Games",
            "body": "Quality over quantity today: play a shorter session and annotate one game immediately after it ends.",
            "priority": "medium",
        },
        {
            "icon": "🎯",
            "title": "One Theme Goal",
            "body": "Pick one tactical theme and look for it in every game. Training one motif at a time compounds faster.",
            "priority": "low",
        },
        {
            "icon": "📓",
            "title": "Post-Game Notes",
            "body": "After each loss, write one sentence: where evaluation turned and why. This improves pattern recall quickly.",
            "priority": "medium",
        },
    ]

    while len(tips) < 3 and generic_pool:
        tips.append(generic_pool.pop(0))

    return tips
