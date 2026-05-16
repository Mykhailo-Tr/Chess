from __future__ import annotations

from io import StringIO
from typing import Any

import chess.pgn
import numpy as np

from app.models import Game


def analyze_time_management(games: list[Game]) -> dict[str, Any]:
    if not games:
        return {
            "average_move_time": 0.0,
            "fast_move_ratio": 0.0,
            "panic_move_ratio": 0.0,
            "time_pressure_score": 0.0,
            "source": "simulated",
        }

    all_move_times: list[float] = []
    panic_samples = 0
    total_samples = 0
    sources: list[str] = []

    for game in games:
        samples = _extract_move_times_from_clock_array(game.clock_data, game.user_color or "white")
        if samples:
            all_move_times.extend(samples["move_times"])
            panic_samples += samples["panic_moves"]
            total_samples += samples["sample_size"]
            sources.append("clock_array")
            continue

        samples = _extract_move_times_from_pgn(game.pgn, game.user_color or "white", game.time_control)
        if samples:
            all_move_times.extend(samples["move_times"])
            panic_samples += samples["panic_moves"]
            total_samples += samples["sample_size"]
            sources.append("pgn")
        else:
            simulated = _simulate_move_times(game)
            all_move_times.extend(simulated)
            panic_samples += sum(1 for v in simulated if v < 2)
            total_samples += len(simulated)
            sources.append("simulated")

    if not all_move_times:
        all_move_times = [0.0]

    values = np.array(all_move_times, dtype=float)
    avg_time = round(float(values.mean()), 2)
    fast_ratio = round(float((values < 3).mean() * 100), 2)
    panic_ratio = round(float((panic_samples / max(total_samples, 1)) * 100), 2)

    score = min(100.0, (fast_ratio * 0.5) + (panic_ratio * 0.8))
    if "clock_array" in sources:
        source = "clock_array"
    elif "pgn" in sources:
        source = "pgn"
    else:
        source = "simulated"

    return {
        "average_move_time": avg_time,
        "fast_move_ratio": fast_ratio,
        "panic_move_ratio": panic_ratio,
        "time_pressure_score": round(float(score), 2),
        "source": source,
    }


def _extract_move_times_from_clock_array(clock_data: Any, user_color: str) -> dict[str, Any] | None:
    if not isinstance(clock_data, list):
        return None
    if not clock_data or not all(isinstance(v, int) for v in clock_data):
        return None

    target_is_white = user_color == "white"
    user_clocks_ms = [
        value for index, value in enumerate(clock_data) if (index % 2 == 0) == target_is_white
    ]

    if len(user_clocks_ms) < 2:
        return None

    move_times = [
        max(0.0, (previous - current) / 1000.0)
        for previous, current in zip(user_clocks_ms, user_clocks_ms[1:])
    ]
    if not move_times:
        return None

    panic_moves = sum(1 for value in user_clocks_ms if value < 10_000)
    return {"move_times": move_times, "panic_moves": panic_moves, "sample_size": len(user_clocks_ms)}


def _extract_move_times_from_pgn(pgn: str, user_color: str, time_control: str | None) -> dict[str, Any] | None:
    if "[%clk" not in pgn:
        return None

    game = chess.pgn.read_game(StringIO(pgn))
    if game is None:
        return None

    increment = _parse_increment(time_control)
    target_white = user_color == "white"

    previous_clock: float | None = None
    move_times: list[float] = []
    panic_moves = 0
    sample_size = 0

    node = game
    ply_index = 0
    while node.variations:
        node = node.variation(0)
        is_white_move = ply_index % 2 == 0
        clock_value = node.clock()
        if clock_value is not None and is_white_move == target_white:
            if previous_clock is not None:
                spent = max(0.0, (previous_clock + increment) - clock_value)
                move_times.append(spent)
            previous_clock = clock_value
            sample_size += 1
            if clock_value < 10:
                panic_moves += 1
        ply_index += 1

    if not move_times:
        return None
    return {"move_times": move_times, "panic_moves": panic_moves, "sample_size": sample_size}


def _parse_increment(time_control: str | None) -> float:
    if not time_control or "+" not in time_control:
        return 0.0
    try:
        _, increment = time_control.split("+", 1)
        return float(increment)
    except ValueError:
        return 0.0


def _simulate_move_times(game: Game) -> list[float]:
    move_count = game.moves_count or 40
    speed = (game.speed or "").lower()
    if speed in {"bullet"}:
        base = 2.0
    elif speed in {"blitz"}:
        base = 4.0
    elif speed in {"rapid"}:
        base = 9.0
    else:
        base = 15.0

    sample_size = max(move_count // 2, 8)
    simulated = np.linspace(base * 0.65, base * 1.25, num=sample_size)
    if game.result == "LOSS":
        simulated = simulated * 0.9
    simulated = np.clip(simulated, 0.2, None)
    return simulated.tolist()
