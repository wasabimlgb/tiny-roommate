# Sprite Sheet Generation Prompt

Generate a single 8×9 grid sprite sheet for the desktop pet.

---

```
Generate a sprite sheet for an animated desktop pet character.

LAYOUT:
- 8 columns × 9 rows grid
- Each cell is a square frame (equal width and height)
- Draw thin (1-2px) grid lines between cells using the same magenta #FF00FF background color — this ensures precise cell boundaries
- Aspect ratio: 8:9
- Recommended output: 4K+ (e.g. 4096×4608, giving 512×512 per frame)

BACKGROUND:
- Every pixel outside the character must be pure magenta #FF00FF
- No gradients, no shadows on background, no texture, no noise
- The character itself must not contain magenta or near-magenta colors (they will be removed during processing)
- No magenta reflections, outlines, or glow on the character

CHARACTER FRAMING:
- Use the framing that best fits each animation — close-up for expressions, full-body for movement
- The character will be displayed small (128×128px), so keep important details readable

ANIMATION:
- Each row is one animation loop; frames progress left to right
- Adjacent frames must transition smoothly — no sudden jumps in position, pose, or expression
- Character should stay centered in each frame (don't drift left/right across frames)
- Keep consistent size and proportions across all 72 frames

ROW DEFINITIONS (top to bottom):
- Row 1: Idle — relaxed, gentle breathing motion, occasional blink. Not static.
- Row 2: Walking — movement animation suggesting walking or moving forward
- Row 3: Looking Around — head/body turning left and right, alert and curious (like watching a screen)
- Row 4: Sleeping — eyes closed, resting pose, gentle breathing. No yawning (it loops). Small zzz okay.
- Row 5: Working — focused expression, sitting at a tiny device/keyboard
- Row 6: Playful — having fun, interacting with a small toy or object, lighthearted energy
- Row 7: Happy — bright expression, joyful body language, small hearts or sparkles
- Row 8: Sad — dejected, looking down, low energy, lonely
- Row 9: Being Held — being picked up or carried, limbs dangling, mildly annoyed or surprised expression

CHARACTER: [describe your character — any animal, creature, or mascot]
STYLE: [describe your preferred style — e.g. "cute, clean, photo-realistic" or "pixel art, retro" or "chibi anime"]
OUTPUT: Only output the sprite sheet image (png or jpg).
```

---

## Processing

After generating, run:
```bash
python3 scripts/process-spritesheet.py input.png -o public/sprites/my_cat.png
```
