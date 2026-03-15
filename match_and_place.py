"""
Step 3: Match artworks to room walls using a scoring system.
Reads rooms_analysis.json + artwork_analysis.json → placement_plan.json
"""

import json
from pathlib import Path


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return (128, 128, 128)
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def color_harmony_score(room_colors: list[str], art_colors: list[str]) -> float:
    """
    Score 0-1 based on how well artwork colors complement room colors.
    Uses basic complementary/analogous color theory.
    """
    if not room_colors or not art_colors:
        return 0.5

    score = 0.0
    comparisons = 0

    for rc in room_colors[:3]:
        for ac in art_colors[:3]:
            try:
                rr, rg, rb = hex_to_rgb(rc)
                ar, ag, ab = hex_to_rgb(ac)

                # Euclidean distance in RGB space
                dist = ((rr - ar) ** 2 + (rg - ag) ** 2 + (rb - ab) ** 2) ** 0.5
                max_dist = (255**2 * 3) ** 0.5  # ~441

                # Sweet spot: not too similar (boring), not too different (clashing)
                # Ideal contrast distance: ~150-280
                normalized = dist / max_dist
                if 0.3 < normalized < 0.65:
                    pair_score = 1.0
                elif normalized <= 0.3:
                    pair_score = normalized / 0.3  # too similar
                else:
                    pair_score = max(0, 1.0 - (normalized - 0.65) / 0.35)  # too different

                score += pair_score
                comparisons += 1
            except Exception:
                continue

    return score / comparisons if comparisons > 0 else 0.5


def style_compatibility_score(room_style: str, art_style: str, art_recommended_rooms: list[str]) -> float:
    """Score style compatibility between room and artwork."""
    score = 0.5

    # Style affinities
    affinities = {
        "modern": ["abstract", "geometric", "minimalist", "digital"],
        "minimalist": ["minimalist", "abstract", "geometric", "photography"],
        "industrial": ["abstract", "expressionist", "photography", "geometric"],
        "scandinavian": ["minimalist", "landscape", "geometric", "watercolor-style"],
        "traditional": ["figurative", "portrait", "landscape", "oil-painting-style"],
        "bohemian": ["abstract", "maximalist", "illustrative", "mixed media"],
    }

    good_styles = affinities.get(room_style, [])
    if any(s in art_style.lower() for s in good_styles):
        score += 0.4

    # Bonus if art explicitly recommends this room type
    # (art_recommended_rooms might be like ["living room", "bedroom"])
    return min(score, 1.0)


def room_type_match_score(room_type: str, art_recommended_rooms: list[str]) -> float:
    """Score whether artwork recommends this room type."""
    if not art_recommended_rooms:
        return 0.5
    room_type_lower = room_type.lower()
    for rec in art_recommended_rooms:
        if rec.lower() in room_type_lower or room_type_lower in rec.lower():
            return 1.0
    return 0.3


def mood_match_score(room_mood: str, art_mood: str) -> float:
    """Score mood compatibility."""
    compatible_moods = {
        "calm": ["calm", "romantic", "melancholic"],
        "energetic": ["energetic", "playful", "dramatic"],
        "cozy": ["calm", "romantic", "warm", "joyful"],
        "formal": ["dramatic", "calm", "mysterious"],
        "playful": ["playful", "energetic", "joyful"],
        "dramatic": ["dramatic", "mysterious", "energetic"],
    }
    good_moods = compatible_moods.get(room_mood, [])
    return 1.0 if art_mood in good_moods else 0.4


def score_pairing(room_data: dict, wall: dict, art_data: dict) -> dict:
    """Compute overall score and explanation for one room-wall + artwork pairing."""

    color_score = color_harmony_score(
        room_data.get("dominant_colors", []),
        art_data.get("dominant_colors", []),
    )
    style_score = style_compatibility_score(
        room_data.get("style", ""),
        art_data.get("style", ""),
        art_data.get("recommended_room_types", []),
    )
    room_match = room_type_match_score(
        room_data.get("room_type", ""),
        art_data.get("recommended_room_types", []),
    )
    mood_score = mood_match_score(
        room_data.get("mood", ""),
        art_data.get("mood", ""),
    )

    # Penalize if wall has obstructions
    obstruction_penalty = 0.2 if wall.get("obstructions", "none") != "none" else 0.0

    # Weighted total
    total = (
        color_score * 0.35
        + style_score * 0.25
        + room_match * 0.25
        + mood_score * 0.15
        - obstruction_penalty
    )

    return {
        "total_score": round(total, 3),
        "breakdown": {
            "color_harmony": round(color_score, 3),
            "style_compatibility": round(style_score, 3),
            "room_type_match": round(room_match, 3),
            "mood_match": round(mood_score, 3),
            "obstruction_penalty": round(obstruction_penalty, 3),
        },
    }


def run(
    rooms_file: str = "rooms_analysis.json",
    artwork_file: str = "artwork_analysis.json",
    output_file: str = "placement_plan.json",
):
    print("\n[Step 3] Matching artworks to walls...")

    with open(rooms_file) as f:
        rooms = json.load(f)
    with open(artwork_file) as f:
        artworks = json.load(f)

    placements = []  # list of best matches
    used_art = set()

    # Build all candidates
    candidates = []
    for room_id, room_data in rooms.items():
        for wall in room_data.get("walls", []):
            if not wall.get("is_best_candidate", False):
                continue
            for art_id, art_data in artworks.items():
                score_data = score_pairing(room_data, wall, art_data)
                candidates.append(
                    {
                        "room_id": room_id,
                        "wall_id": wall["id"],
                        "art_id": art_id,
                        "room_image": room_data["source_image"],
                        "art_image": art_data["source_image"],
                        "wall": wall,
                        "score": score_data["total_score"],
                        "score_breakdown": score_data["breakdown"],
                        "room_type": room_data.get("room_type"),
                        "room_style": room_data.get("style"),
                        "art_style": art_data.get("style"),
                        "art_mood": art_data.get("mood"),
                        "art_title": art_data.get("title_guess"),
                        "matting": art_data.get("matting_suggestion"),
                        "design_notes": art_data.get("design_notes"),
                        "room_notes": room_data.get("general_notes"),
                    }
                )

    # Greedy assignment: best score first, each art used once, each wall used once
    used_walls = set()
    candidates.sort(key=lambda x: x["score"], reverse=True)

    for c in candidates:
        key_wall = f"{c['room_id']}_{c['wall_id']}"
        if c["art_id"] in used_art or key_wall in used_walls:
            continue
        placements.append(c)
        used_art.add(c["art_id"])
        used_walls.add(key_wall)

    with open(output_file, "w") as f:
        json.dump(placements, f, indent=2)

    print(f"  Found {len(placements)} placement(s):")
    for p in placements:
        print(
            f"    → '{p['art_title']}' into {p['room_type']} / {p['wall_id']}  "
            f"[score: {p['score']}]"
        )

    print(f"\n  Saved placement plan → {output_file}")
    return placements


if __name__ == "__main__":
    run()
