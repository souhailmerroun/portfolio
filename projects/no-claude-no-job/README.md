# No Claude, No Job

A coding challenge game that only unlocks when Claude is down.

**Live**: [no-claude-no-job.vercel.app](https://no-claude-no-job.vercel.app)

## What it does

The app polls Anthropic's status page every 60 seconds. When all systems are operational, the game is locked — go do your job. When Claude has an incident, it unlocks and throws programming one-liners at you across 12 languages (JavaScript, TypeScript, React, Python, PHP, Go, Rust, Java, C#, Ruby, Bash, SQL).

Answer normalization strips whitespace and compares against multiple accepted forms so `const x = 1;` and `const x=1` both pass.

After each answer you can generate a shareable OG image (rendered client-side on a `<canvas>`) and copy it to clipboard.

## Stack

- **Next.js 16** / **React 19** / **TypeScript 5** — App Router, server components for layout, client component for game state
- **Tailwind CSS 4** — utility-first styling, no custom CSS beyond resets
- **Vercel** — zero-config deployment, edge function for status proxy
- **Canvas API** — client-side OG image generation for share cards

## Architecture

```
app/
  layout.tsx          Root layout (Geist font, metadata)
  page.tsx            Game UI — all state via useState/useEffect
  challenges.ts       Challenge bank + answer normalizer
  globals.css         Tailwind base
  api/status/route.ts Server-side proxy to status.anthropic.com
```

The status check runs server-side (API route) to avoid CORS issues with Anthropic's status endpoint. Game logic is entirely client-side — no database, no auth, no server state.

## Key patterns

- **Conditional rendering chain**: loading → locked → language picker → challenge — clean state machine without a reducer
- **Answer normalization**: whitespace-insensitive comparison via regex that strips padding around operators
- **Canvas share image**: 1200×630 OG-sized PNG generated in-browser with word wrapping, no server round-trip
