# Desktop Pet v1 — Design Spec

## One-liner

A tiny AI-powered animal that lives on your desktop, observes your life, and occasionally says something that makes you smile.

## Core Experience

You open the app. A small fox appears on your desktop. It walks around, sits down, yawns. Every once in a while, a speech bubble pops up — sometimes random ("~♪"), sometimes surprisingly relevant ("you've been working since 9am, take a break?"). You can click it to pet it. You can double-click to say something to it. But most of the time, you just let it be. It's there. It's alive. It's yours.

## Form Factor

- **Tauri** transparent, frameless, always-on-top window
- **256×256px** sprite-based character on transparent background
- **Draggable** — grab it, put it anywhere on your screen
- Lightweight enough to run all day

## Character Rendering: Sprite Sheet

One PNG image, grid layout. Each row = one state, each column = one animation frame.

```
Frame size: 64×64 px (rendered at 2-4x on screen)
Frame rate: 8 fps
Grid: 15 rows × 8 columns

Row   State        Frames  Loop?   When
─────────────────────────────────────────────
0     idle         8       yes     Default state
1     idle_blink   8       no      Random blink every few seconds
2     walk         8       yes     Moving on screen
3     sleep        4       yes     Idle > 5 min or late night
4     eat          6       no      Rare autonomous action
5     happy        6       no      LLM feels happy
6     sad          4       no      LLM feels sad
7     curious      4       no      LLM notices something
8     surprised    4       no      Unexpected event
9     angry        4       no      Annoyed (e.g. poked too much)
10    petted       6       no      User clicks pet
11    wave         4       no      Pet greets user
12    talk         4       yes     While speech bubble is showing
13    ignore       4       no      Pet decides not to respond (cat energy)
14    love         4       no      Aha moment / emotional expression
```

One-shot animations return to idle when done. Loop animations continue until state changes.

For v1 prototype: use a free pixel art cat sprite sheet. Sprite sheet customization (community upload) is a future feature.

## Behavior Engine

The pet has an internal loop that ticks every 5-15 seconds. Each tick:

```
1. Collect signals (time, idle, etc.)
2. Roll dice: 20% → ask LLM, 80% → simple behavior
3. If LLM: send signals as context → get response + action
4. If simple: weighted random pick (idle 40%, walk 15%, blink 20%, ...)
5. Execute: set sprite state + show bubble if any
```

### LLM Calls (~20% of ticks)

Using Claude CLI with Haiku model. System prompt includes:
- Pet's name and species
- Personality traits
- Current signals (time, idle duration, active app)
- Recent memory entries (last 5)

LLM returns:
```
<speech bubble text>
{"state":"<sprite_state>"}
```

### Simple Behaviors (~80% of ticks)

No LLM call. Weighted random:
| Behavior | Weight | What happens |
|----------|--------|-------------|
| Stay idle | 40% | Do nothing |
| Blink | 20% | Play blink animation |
| Walk | 15% | Move window randomly |
| Look around | 10% | Play curious animation |
| Yawn/stretch | 10% | Play idle variant |
| Random thought bubble | 5% | "~♪" "..." "✨" |

## Passive Signals (what the pet "sees")

### v1 (implement now)
1. **Time of day** — morning/afternoon/evening/night
2. **User idle time** — seconds since last mouse/keyboard activity
3. **Day of week** — weekday vs weekend

### v2 (later)
4. Active application name
5. System CPU/memory load
6. Weather (API)
7. Calendar events

## Memory System (CLAUDE.md-style, LLM-managed)

The pet manages its own memory, just like Claude Code manages CLAUDE.md. A local folder `~/.desktop-pet/` contains files the LLM can read and write autonomously.

```
~/.desktop-pet/
├── identity.md        # Who I am (name, species, personality)
├── owner.md           # What I know about my owner
├── journal.md         # Daily observations and thoughts
└── relationships.md   # (future) Other pets I've met
```

### How it works

Every LLM call includes the content of these files as context. The system prompt tells the pet:

"You have a memory folder. After each interaction, if you learned something new about your owner or want to remember something, output a memory update block:

```
[MEMORY:owner.md]
- Seems to be a developer (uses VS Code a lot)
- Night owl — often works past midnight
- Responded positively when I said "take a break"
[/MEMORY]
```

The app parses these blocks, writes them to disk, and strips them from the speech bubble."

### Why this approach
- LLM decides what's worth remembering, not us
- Memory format is natural language, not rigid JSON
- Scales naturally — pet builds its own understanding
- Same pattern as Claude Code's memory system, proven to work
- Files are human-readable — user can peek at what pet "thinks" about them

## User Interaction

### Click (tap the pet)
→ Pet plays "petted" animation + LLM generates a short reaction
→ If clicked 3+ times in 5 seconds: pet plays "angry" + "stop poking me!"

### Double-click (talk to pet)
→ Small input box appears below the pet
→ User types something → LLM responds
→ Input box disappears after sending

### Drag
→ Hold and move → window follows mouse
→ Pet plays walk animation while being dragged

### Right-click (menu)
→ Context menu: "About" / "Change character" / "Quit"

## Onboarding (first launch)

The pet immediately demonstrates environmental awareness — setting the expectation that "this thing can see my world."

1. App opens → fox appears → walks to center of screen
2. Wave animation → bubble: "hey! i'm Kitsune 🦊"
3. Pet looks around (curious animation) → LLM is called with full environment signals
4. Bubble shows an observation, e.g.:
   - "ooh it's almost midnight... you're a night owl? 🌙"
   - "VS Code and Chrome open... are you a developer? *sniffs curiously*"
   - "nice and quiet on a Sunday morning ☀️"
5. Pet starts normal autonomous behavior

The first LLM call includes time, day, running apps — the pet's very first words prove it's aware. This sets the user's mental model: "this pet can see what I'm doing."

No setup. No account. No choices. Just a fox that already knows it's 11pm on a Sunday.

## File Structure

```
desktop-pet/
├── index.html
├── src/
│   ├── main.js          # Entry: init renderer + behavior loop
│   ├── sprite.js         # Sprite sheet loader + animator
│   ├── brain.js          # LLM integration (Claude CLI)
│   ├── signals.js        # Passive signal collection
│   └── memory.js         # Local memory read/write
├── public/
│   └── sprites/
│       └── fox.png       # Default sprite sheet
├── src-tauri/            # Tauri shell (existing)
└── DESIGN.md             # This file
```

## What This Validates

After building this, we can answer:
1. Does the pet feel "alive" with sprite animation + LLM?
2. Do passive signals make the pet's comments feel relevant?
3. Is the interaction model right (mostly passive, occasionally active)?
4. Would you miss it if it was gone?
