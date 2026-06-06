"use client";

import { useEffect, useMemo, useState } from "react";
import { CHALLENGES, LANGUAGES, isCorrect, type Challenge, type Language } from "./challenges";

type StatusResponse = { isDown: boolean; indicator: string; description: string };

function pickChallenge(language: Language, exclude?: Challenge): Challenge {
  const all = CHALLENGES.filter((c) => c.language === language);
  const pool = exclude && all.length > 1 ? all.filter((c) => c !== exclude) : all;
  return pool[Math.floor(Math.random() * pool.length)];
}

export default function Page() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [language, setLanguage] = useState<Language | null>(null);
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [input, setInput] = useState("");
  const [result, setResult] = useState<"correct" | "wrong" | null>(null);
  const [score, setScore] = useState(0);
  const [streak, setStreak] = useState(0);
  const [shared, setShared] = useState<"idle" | "copied" | "error">("idle");

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/status", { cache: "no-store" });
      const data: StatusResponse = await res.json();
      setStatus(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const id = setInterval(fetchStatus, 60_000);
    return () => clearInterval(id);
  }, []);

  const chooseLanguage = (lang: Language) => {
    setLanguage(lang);
    setChallenge(pickChallenge(lang));
    setInput("");
    setResult(null);
  };

  const submit = () => {
    if (!challenge) return;
    if (isCorrect(input, challenge.answers)) {
      setResult("correct");
      setScore((s) => s + 1);
      setStreak((s) => s + 1);
    } else {
      setResult("wrong");
      setStreak(0);
    }
  };

  const next = () => {
    if (!language) return;
    setChallenge((c) => pickChallenge(language, c ?? undefined));
    setInput("");
    setResult(null);
    setShared("idle");
  };

  const resetLanguage = () => {
    setLanguage(null);
    setChallenge(null);
    setInput("");
    setResult(null);
    setShared("idle");
  };

  const share = async () => {
    if (!challenge || !result) return;
    try {
      const blob = await renderShareImage({
        language: challenge.language,
        prompt: challenge.prompt,
        correct: result === "correct",
        score,
        streak,
      });
      if (navigator.clipboard && "write" in navigator.clipboard && typeof ClipboardItem !== "undefined") {
        await navigator.clipboard.write([new ClipboardItem({ "image/png": blob })]);
      } else {
        const text = `No Claude, No Job — ${challenge.language} · ${result === "correct" ? "✓ solo-coded" : "✗ stumped"} · score ${score}. https://no-claude-no-job.vercel.app`;
        await navigator.clipboard.writeText(text);
      }
      setShared("copied");
      setTimeout(() => setShared("idle"), 2000);
    } catch {
      setShared("error");
      setTimeout(() => setShared("idle"), 2000);
    }
  };

  const canPlay = status?.isDown === true;
  const statusLabel = useMemo(() => status?.description ?? "", [status]);

  return (
    <main className="min-h-screen bg-white text-neutral-900 antialiased">
      <div className="mx-auto max-w-2xl px-6 py-16">
        <header className="mb-12">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-semibold tracking-tight">No Claude, No Job</h1>
            <StatusPill loading={loading} isDown={status?.isDown} label={statusLabel} />
          </div>
          <p className="mt-3 text-sm text-neutral-500">
            A reminder that you can still code without an AI. Playable only when Claude has issues.
          </p>
        </header>

        {loading && !status && <Skeleton />}

        {status && !canPlay && <Locked onRefresh={fetchStatus} label={statusLabel} />}

        {status && canPlay && !language && <LanguagePicker onPick={chooseLanguage} />}

        {status && canPlay && language && challenge && (
          <section>
            <div className="mb-6 flex items-center justify-between text-xs uppercase tracking-wider text-neutral-500">
              <button
                onClick={resetLanguage}
                className="hover:text-neutral-900"
              >
                ← Change language
              </button>
              <div className="flex gap-6">
                <span>Score {score}</span>
                <span>Streak {streak}</span>
              </div>
            </div>

            <div className="rounded-2xl border border-neutral-200 p-8">
              <div className="mb-2 text-xs font-medium uppercase tracking-wider text-neutral-400">
                {challenge.language}
              </div>
              <h2 className="text-lg font-medium leading-snug">{challenge.prompt}</h2>

              <textarea
                value={input}
                onChange={(e) => {
                  setInput(e.target.value);
                  if (result) setResult(null);
                }}
                onKeyDown={(e) => {
                  if ((e.metaKey || e.ctrlKey) && e.key === "Enter") submit();
                }}
                spellCheck={false}
                placeholder="Type a one-liner…"
                className="mt-6 h-28 w-full resize-none rounded-lg border border-neutral-200 bg-white p-4 font-mono text-sm text-neutral-900 outline-none transition focus:border-neutral-400"
              />

              <div className="mt-4 flex items-center gap-3">
                <button
                  onClick={submit}
                  disabled={!input.trim() || result !== null}
                  className="rounded-lg bg-neutral-900 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-neutral-700 disabled:cursor-not-allowed disabled:bg-neutral-300"
                >
                  Submit
                </button>
                <button
                  onClick={next}
                  className="rounded-lg border border-neutral-200 px-5 py-2.5 text-sm font-medium text-neutral-700 transition hover:border-neutral-400"
                >
                  {result ? "Next" : "Skip"}
                </button>
                <span className="ml-auto text-xs text-neutral-400">⌘ + Enter</span>
              </div>

              {result && (
                <div className="mt-6 rounded-lg border border-neutral-200 p-4">
                  <div className={`text-sm font-medium ${result === "correct" ? "text-emerald-600" : "text-red-600"}`}>
                    {result === "correct" ? "Correct" : "Not quite"}
                  </div>
                  <div className="mt-1 text-sm text-neutral-600">
                    {result === "correct"
                      ? "You didn't need the AI for that one."
                      : "Try again, skip, or share anyway."}
                  </div>
                  <div className="mt-4 flex items-center gap-2">
                    <button
                      onClick={share}
                      className="rounded-md bg-neutral-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-neutral-700"
                    >
                      {shared === "copied"
                        ? "Copied to clipboard ✓"
                        : shared === "error"
                        ? "Copy failed"
                        : "Share →"}
                    </button>
                    <span className="text-xs text-neutral-400">Copies an image you can paste anywhere</span>
                  </div>
                </div>
              )}
            </div>
          </section>
        )}

        <footer className="mt-16 text-xs text-neutral-400">
          Status polled from status.anthropic.com every minute.
        </footer>
      </div>
    </main>
  );
}

function LanguagePicker({ onPick }: { onPick: (l: Language) => void }) {
  return (
    <section>
      <h2 className="mb-1 text-lg font-medium">Pick your language</h2>
      <p className="mb-6 text-sm text-neutral-500">We&apos;ll throw one-liners at you in that language.</p>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {LANGUAGES.map((l) => (
          <button
            key={l}
            onClick={() => onPick(l)}
            className="rounded-xl border border-neutral-200 bg-white px-4 py-5 text-sm font-medium text-neutral-800 transition hover:border-neutral-900 hover:bg-neutral-50"
          >
            {l}
          </button>
        ))}
      </div>
    </section>
  );
}

function StatusPill({
  loading,
  isDown,
  label,
}: {
  loading: boolean;
  isDown: boolean | undefined;
  label: string;
}) {
  const dot = loading ? "bg-neutral-300" : isDown ? "bg-red-500" : "bg-emerald-500";
  const text = loading ? "Checking…" : label || (isDown ? "Claude down" : "Claude operational");
  return (
    <div className="flex items-center gap-2 rounded-full border border-neutral-200 px-3 py-1 text-xs text-neutral-600">
      <span className={`inline-block h-2 w-2 rounded-full ${dot}`} />
      {text}
    </div>
  );
}

function Skeleton() {
  return (
    <div className="rounded-2xl border border-neutral-200 p-8">
      <div className="h-4 w-24 animate-pulse rounded bg-neutral-100" />
      <div className="mt-4 h-6 w-3/4 animate-pulse rounded bg-neutral-100" />
      <div className="mt-6 h-28 w-full animate-pulse rounded bg-neutral-100" />
    </div>
  );
}

function Locked({ onRefresh, label }: { onRefresh: () => void; label: string }) {
  return (
    <section className="rounded-2xl border border-neutral-200 p-10 text-center">
      <div className="mx-auto mb-5 flex h-12 w-12 items-center justify-center rounded-full bg-neutral-50 text-2xl">
        🔒
      </div>
      <h2 className="text-xl font-medium">Claude is working</h2>
      <p className="mx-auto mt-2 max-w-sm text-sm text-neutral-500">
        Go do your job. This game only unlocks when Anthropic&apos;s status page reports an
        incident.
      </p>
      <p className="mt-4 text-xs text-neutral-400">
        Current status: {label || "All systems operational"}
      </p>
      <button
        onClick={onRefresh}
        className="mt-8 rounded-lg border border-neutral-200 px-4 py-2 text-sm font-medium text-neutral-700 transition hover:border-neutral-400"
      >
        Check again
      </button>
    </section>
  );
}

async function renderShareImage(opts: {
  language: string;
  prompt: string;
  correct: boolean;
  score: number;
  streak: number;
}): Promise<Blob> {
  const W = 1200;
  const H = 630;
  const canvas = document.createElement("canvas");
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext("2d")!;

  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, W, H);

  ctx.strokeStyle = "#e5e5e5";
  ctx.lineWidth = 2;
  ctx.strokeRect(32, 32, W - 64, H - 64);

  ctx.fillStyle = "#171717";
  ctx.font = "600 44px ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto";
  ctx.fillText("No Claude, No Job", 80, 130);

  ctx.fillStyle = "#737373";
  ctx.font = "400 22px ui-sans-serif, system-ui, -apple-system";
  ctx.fillText(opts.language.toUpperCase(), 80, 180);

  ctx.fillStyle = "#171717";
  ctx.font = "500 36px ui-sans-serif, system-ui, -apple-system";
  wrapText(ctx, opts.prompt, 80, 260, W - 160, 48);

  const tag = opts.correct ? "Solo-coded ✓" : "Stumped ✗";
  const tagColor = opts.correct ? "#059669" : "#dc2626";
  ctx.fillStyle = tagColor;
  ctx.font = "600 28px ui-sans-serif, system-ui, -apple-system";
  ctx.fillText(tag, 80, H - 120);

  ctx.fillStyle = "#737373";
  ctx.font = "400 20px ui-sans-serif, system-ui, -apple-system";
  ctx.fillText(`Score ${opts.score}  ·  Streak ${opts.streak}`, 80, H - 80);

  ctx.fillStyle = "#a3a3a3";
  ctx.font = "400 18px ui-sans-serif, system-ui, -apple-system";
  const url = "no-claude-no-job.vercel.app";
  const urlW = ctx.measureText(url).width;
  ctx.fillText(url, W - 80 - urlW, H - 80);

  return await new Promise<Blob>((resolve, reject) => {
    canvas.toBlob((b) => (b ? resolve(b) : reject(new Error("toBlob failed"))), "image/png");
  });
}

function wrapText(
  ctx: CanvasRenderingContext2D,
  text: string,
  x: number,
  y: number,
  maxWidth: number,
  lineHeight: number,
) {
  const words = text.split(" ");
  let line = "";
  let yy = y;
  for (const w of words) {
    const test = line ? line + " " + w : w;
    if (ctx.measureText(test).width > maxWidth && line) {
      ctx.fillText(line, x, yy);
      line = w;
      yy += lineHeight;
    } else {
      line = test;
    }
  }
  if (line) ctx.fillText(line, x, yy);
}
