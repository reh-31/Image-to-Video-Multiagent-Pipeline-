"""Style guide documents — one entry per visual style, used as RAG chunks.

Each document covers: pacing, color treatment, caption style, transition
preference, and animation style.  One document = one Chroma chunk.
"""

STYLE_GUIDE_DOCS: list[str] = [
    # ── cinematic_wedding ────────────────────────────────────────────────────
    """Style: cinematic_wedding
Pacing: Slow, lingering shots (4–6 seconds per scene). Allow emotions to breathe.
Color Treatment: Warm, golden-hour tones with slight desaturation on shadows.
  Use LUT-style color grading: lifted blacks, peachy highlights.
Caption Style: Minimal, italic lowercase captions. Emotional, poetic language.
  Example: "forever begins here" or "two families, one love."
Transition Preference: Slow dissolves (fade) and occasional dip-to-white.
  Avoid hard cuts unless emphasizing a vow moment.
Animation Style: Subtle Ken Burns (slow zoom-in or pan) on still images.
  Prefer ease-in-out interpolation. No aggressive motion.
Narrative Arc: Build from quiet arrival → intimate ceremony → joyful celebration.
Music Suggestion: Orchestral strings, piano, or acoustic guitar.""",

    # ── upbeat_birthday ──────────────────────────────────────────────────────
    """Style: upbeat_birthday
Pacing: Fast and energetic (1–2 seconds per scene). Keep momentum high.
Color Treatment: Vibrant, saturated colors. Boost yellows and magentas.
  Use high-contrast treatment to make subjects pop.
Caption Style: Bold, all-caps captions with exclamation marks.
  Example: "SURPRISE!", "BEST DAY EVER!", "PARTY TIME!"
Transition Preference: Quick cuts, pop zooms, and slide transitions.
  Match cuts to beat of upbeat music track.
Animation Style: Bouncy spring animations (zoom-in with overshoot).
  Use scale animations: from 0.8 to 1.0 with spring physics.
Narrative Arc: Open with surprise → candid laughter → cake → group shots.
Music Suggestion: Upbeat pop, indie rock, or funk with strong beat.""",

    # ── corporate_highlights ─────────────────────────────────────────────────
    """Style: corporate_highlights
Pacing: Medium, professional (2–4 seconds per scene). Deliberate and polished.
Color Treatment: Clean, neutral color palette. Slight blue-teal grade.
  Avoid oversaturation. Keep skin tones accurate and professional.
Caption Style: Professional, sentence-case with company branding in mind.
  Example: "Q3 Product Launch" or "Team Excellence Award 2024."
Transition Preference: Clean slides (left-to-right) or subtle fades.
  Consistent transition direction throughout the video.
Animation Style: Slide-in animations for text overlays. Smooth linear easing.
  Lower-third style captions with background bar.
Narrative Arc: Opening brand moment → key milestones → team recognition → CTA.
Music Suggestion: Ambient corporate, light electronic, or soft orchestral.""",

    # ── minimal_clean ────────────────────────────────────────────────────────
    """Style: minimal_clean
Pacing: Slow to medium (3–5 seconds per scene). Intentional breathing room.
Color Treatment: Desaturated, near-monochrome with one accent color.
  High-key lighting, clean whites, and airy aesthetics.
Caption Style: Thin sans-serif font, small size. Lowercase, no punctuation.
  Example: "light and shadow" or "a quiet afternoon."
Transition Preference: Simple fade to white or pure cut. No flashy effects.
  Consistency is more important than variety.
Animation Style: Ultra-subtle opacity fade or slow horizontal drift.
  Avoid any scale or rotation animations.
Narrative Arc: Single mood or concept across all scenes. No strong arc.
Music Suggestion: Ambient drone, lo-fi, or silence with occasional sound design.""",

    # ── dramatic_emotional ───────────────────────────────────────────────────
    """Style: dramatic_emotional
Pacing: Variable — slow during emotional peaks (5–6s), faster during
  transitions (1–2s). Contrast creates impact.
Color Treatment: High-contrast, cinematic grade with deep shadows and
  crushed blacks. Cool tones for sadness, warm for warmth and hope.
Caption Style: Emotional, first-person or lyrical. Medium font weight.
  Example: "in your eyes, I found home" or "a journey worth every step."
Transition Preference: Cross-dissolves for emotional moments, hard cuts for
  dramatic reveals. Use zoom-out transitions for endings.
Animation Style: Slow zoom-in (Ken Burns) during emotional pauses.
  Use fadeIn with longer duration (1.5–2s).
Narrative Arc: Problem/longing → journey → emotional resolution.
Music Suggestion: Cinematic score, strings with swell, or emotional piano.""",

    # ── energetic_party ──────────────────────────────────────────────────────
    """Style: energetic_party
Pacing: Very fast (0.5–1.5 seconds per scene). Beat-synced editing.
Color Treatment: Super-saturated, neon-influenced palette.
  Push vibrance to maximum, add slight vignette for club feel.
Caption Style: Bold, large, colorful captions. Emoji-style language.
  Example: "🎉 LET'S GO!", "GOOD VIBES ONLY", "NIGHT TO REMEMBER!"
Transition Preference: Hard cuts and zoom transitions that match the beat.
  Flash frames and glitch effects are acceptable.
Animation Style: Quick scale-pop animations (0.5 → 1.0 in 3 frames).
  Rotation animations and perspective skew are welcome.
Narrative Arc: Energy build → peak chaos → memorable moments → aftermath.
Music Suggestion: EDM, hip-hop, or dance-pop with strong 4/4 beat.""",
]
