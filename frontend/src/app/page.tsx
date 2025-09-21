"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
const API_BASE = "https://backend.rlab-ai.yeezus.live";





function useMicRecorder(onFinish: (blob: Blob) => void) {
  const [supported, setSupported] = useState<boolean>(true);
  const [recording, setRecording] = useState(false);
  const [durationMs, setDurationMs] = useState(0);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const timerRef = useRef<any>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    // Check support (Safari desktop/iOS might be false)
    const ok = typeof window !== "undefined" && "MediaRecorder" in window && navigator?.mediaDevices?.getUserMedia;
    setSupported(!!ok);
  }, []);

  const start = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Try preferred codec; fallback if needed
      const mimeCandidates = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/mp4',
        'audio/mpeg',
        'audio/wav'
      ];
      const mimeType = mimeCandidates.find((m) => MediaRecorder.isTypeSupported?.(m)) || '';

      const rec = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      mediaRef.current = rec;
      chunksRef.current = [];

      rec.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
      };
      rec.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: rec.mimeType || 'audio/webm' });
        onFinish(blob);
        // cleanup stream tracks
        stream.getTracks().forEach(t => t.stop());
        streamRef.current = null;
      };

      rec.start(250); // gather chunks every 250ms
      setRecording(true);
      setDurationMs(0);
      timerRef.current = setInterval(() => setDurationMs((d) => d + 1000), 1000);
    } catch (err) {
      console.error(err);
      alert("Microphone permission denied or unsupported browser.");
    }
  };

  const stop = () => {
    if (mediaRef.current && mediaRef.current.state !== "inactive") {
      mediaRef.current.stop();
    }
    if (timerRef.current) clearInterval(timerRef.current);
    setRecording(false);
  };

  useEffect(() => () => {
    // unmount cleanup
    if (timerRef.current) clearInterval(timerRef.current);
    streamRef.current?.getTracks().forEach(t => t.stop());
  }, []);

  return { supported, recording, durationMs, start, stop };
}


// const [Chatopen,setChatOpen]=useState(false)
// useEffect(() => {
//   setChatOpen(false); // collapse chat on first render
// }, []);
// add near your other helpers in page.tsx
async function sttUpload(file: File) {
  const form = new FormData();
  form.append("audio", file);
  const res = await fetch(`${API_BASE}/api/stt/upload`, { method: "POST", body: form });
  const text = await res.text();
  const data = JSON.parse(text);
  if (!res.ok) throw new Error(data.error || "upload failed");
  return data.upload_url as string;
}

async function sttStart(upload_url: string) {
  const res = await fetch(`${API_BASE}/api/stt/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ upload_url }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "start failed");
  return data.id as string;
}

async function sttPoll(id: string, onTick?: (s: string) => void): Promise<string> {
  while (true) {
    const res = await fetch(`${API_BASE}/api/stt/status?id=${encodeURIComponent(id)}`);
    const data = await res.json();
    if (onTick) onTick(data.status);
    if (data.status === "completed") return data.text || "";
    if (data.status === "error") throw new Error(data.error || "transcription error");
    await new Promise(r => setTimeout(r, 2000));
  }
}




// put near top of page.tsx
async function readBody(res: Response) {
  const text = await res.text();
  try {
    const json = JSON.parse(text);
    return { ok: true, json, text };
  } catch {
    return { ok: false, json: null, text };
  }
}

/* ---------- tiny helpers ---------- */
const cx = (dark: string, light: string, theme: "dark" | "light") =>
  theme === "dark" ? dark : light;

/* ---------- UI atoms ---------- */
function ProgressBar({
  value,
  theme,
}: {
  value: number;
  theme: "dark" | "light";
}) {
  return (
    <div
      className={cx(
        "flex-1 h-1.5 bg-neutral-800 rounded-full overflow-hidden",
        "flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden",
        theme,
      )}
    >
      <div
        className={cx("h-full bg-sky-500/70", "h-full bg-indigo-500/70", theme)}
        style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
      />
    </div>
  );
}

function Chip({
  text,
  tone = "warn",
  theme,
}: {
  text: string;
  tone?: "warn" | "ok";
  theme: "dark" | "light";
}) {
  const warn = cx(
    "bg-red-500/10 border-red-500/20 text-red-300",
    "bg-red-100 border-red-200 text-red-700",
    theme,
  );
  const ok = cx(
    "bg-emerald-500/10 border-emerald-500/20 text-emerald-300",
    "bg-emerald-100 border-emerald-200 text-emerald-700",
    theme,
  );
  const cls = tone === "warn" ? warn : ok;
  return (
    <span className={`px-3 py-1 rounded-full border text-xs ${cls}`}>
      {text}
    </span>
  );
}

function SectionCard({
  title,
  children,
  theme,
}: {
  title: string;
  children: React.ReactNode;
  theme: "dark" | "light";
}) {
  return (
    <div
      className={cx(
        "rounded-2xl border border-neutral-800 bg-black/30 p-4",
        "rounded-2xl border border-gray-200 bg-white p-4 shadow-sm",
        theme,
      )}
    >
      <h4
        className={cx(
          "font-medium mb-2 text-neutral-100",
          "font-medium mb-2 text-gray-900",
          theme,
        )}
      >
        {title}
      </h4>
      {children}
    </div>
  );
}

function Chips({
  items,
  tone = "default",
  theme,
}: {
  items: string[];
  tone?: "default" | "warn";
  theme: "dark" | "light";
}) {
  if (!items?.length) return null;
  const cls =
    tone === "warn"
      ? cx(
          "bg-red-500/10 border-red-500/20 text-red-300",
          "bg-red-100 border-red-200 text-red-700",
          theme,
        )
      : cx(
          "bg-neutral-700/20 border-neutral-600 text-neutral-200",
          "bg-indigo-100 border-indigo-200 text-indigo-700",
          theme,
        );
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((x, i) => (
        <span
          key={i}
          className={`px-3 py-1 rounded-full border text-xs ${cls}`}
        >
          {x}
        </span>
      ))}
    </div>
  );
}

function DotList({
  items,
  theme,
}: {
  items: string[];
  theme: "dark" | "light";
}) {
  if (!items?.length) return null;
  return (
    <ul
      className={cx(
        "text-neutral-300 space-y-1",
        "text-gray-700 space-y-1",
        theme,
      )}
    >
      {items.map((t, i) => (
        <li key={i} className="flex items-start gap-2">
          <span
            className={cx("text-sky-400 mt-1", "text-indigo-500 mt-1", theme)}
          >
            •
          </span>
          <span>{t}</span>
        </li>
      ))}
    </ul>
  );
}

function Gauge({ value, theme }: { value: number; theme: "dark" | "light" }) {
  const deg = Math.max(0, Math.min(100, value)) * 3.6;
  const ring = theme === "dark" ? "rgb(34 211 238)" : "rgb(99 102 241)";
  return (
    <div className="relative h-28 w-28 rounded-full grid place-items-center">
      <div
        className="absolute inset-0 rounded-full"
        style={{
          background: `conic-gradient(${ring} ${deg}deg, ${
            theme === "dark" ? "rgb(24 24 27)" : "rgb(229 231 235)"
          } 0deg)`,
        }}
      />
      <div
        className={cx(
          "absolute inset-2 rounded-full bg-neutral-950 border border-neutral-800 grid place-items-center",
          "absolute inset-2 rounded-full bg-white border border-gray-200 grid place-items-center",
          theme,
        )}
      >
        <div className="text-center">
          <div
            className={cx(
              "text-2xl font-bold text-sky-300",
              "text-2xl font-bold text-indigo-600",
              theme,
            )}
          >
            {Math.round(value)}
          </div>
          <div
            className={cx(
              "text-[10px] tracking-wide text-neutral-400",
              "text-[10px] tracking-wide text-gray-500",
              theme,
            )}
          >
            Critique
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------- parsing helpers ---------- */
function parseCritique(raw: string) {
  try {
    const obj = JSON.parse(raw);
    if (obj && typeof obj === "object") {
      return {
        meta: obj.meta ?? { title: "", description: "", domain: "" },
        scores: obj.scores ?? {
          novelty: undefined,
          feasibility: undefined,
          impact: undefined,
          overall: undefined,
        },
        reasons: obj.reasons ?? {
          noveltyReason: "",
          feasibilityReason: "",
          impactReason: "",
        },
        gaps: Array.isArray(obj.gaps) ? obj.gaps : [],
        suggestions: Array.isArray(obj.suggestions) ? obj.suggestions : [],
        verdict: obj.verdict ?? "",
        raw,
      };
    }
  } catch {}
  // Fallback parsing logic...
  return {
    meta: { title: "", description: "", domain: "" },
    scores: {
      novelty: undefined,
      feasibility: undefined,
      impact: undefined,
      overall: undefined,
    },
    reasons: { noveltyReason: "", feasibilityReason: "", impactReason: "" },
    gaps: [],
    suggestions: [],
    verdict: "",
    raw,
  };
}

function parseLiterature(raw: string) {
  try {
    return JSON.parse(raw);
  } catch {
    return { raw };
  }
}

function parseCommunity(raw: string) {
  try {
    return JSON.parse(raw);
  } catch {
    return { raw };
  }
}

function parseDirections(raw: string) {
  try {
    return JSON.parse(raw);
  } catch {
    return { raw };
  }
}

function parseDraft(raw: string) {
  try {
    return JSON.parse(raw);
  } catch {
    return { raw };
  }
}

/* ---------- tiny components ---------- */
function Toast({ text, theme }: { text: string; theme: "dark" | "light" }) {
  return (
    <div
      className={cx(
        "rounded-xl bg-neutral-900/80 backdrop-blur border border-neutral-800 px-3 py-2 text-sm shadow text-white",
        "rounded-xl bg-white/90 backdrop-blur border border-gray-200 px-3 py-2 text-sm shadow text-gray-900",
        theme,
      )}
    >
      {text}
    </div>
  );
}

function useShortcuts(actions: {
  analyze: () => void;
  reset: () => void;
  openChat: () => void;
  exportDraft: () => void;
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        actions.openChat();
      }
      if (
        e.key === "Enter" &&
        (document.activeElement?.tagName !== "TEXTAREA" ||
          e.metaKey ||
          e.ctrlKey)
      ) {
        actions.analyze();
      }
      if (e.key === "Escape") actions.reset();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [actions]);
}

/* =========================================================
   PAGE
========================================================= */
export default function Page() {
  const [idea, setIdea] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [running, setRunning] = useState(false);
  const [activeStep, setActiveStep] = useState<number>(-1);
  const [chatOpen, setChatOpen] = useState(true);
  const [messages, setMessages] = useState<
    { role: "user" | "agent"; text: string }[]
  >([]);
  const [toasts, setToasts] = useState<string[]>([]);
  const [critiqueScore, setCritiqueScore] = useState<number | null>(null);
  const [model, setModel] = useState("Gemini 1.5 Flash");
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  type FileInfo = { name: string; size: number; type: string; url?: string };
  const [files, setFiles] = useState<FileInfo[]>([]);

  const [critiqueParsed, setCritiqueParsed] = useState<ReturnType<
    typeof parseCritique
  > | null>(null);
  const [litParsed, setLitParsed] = useState<any>(null);

  const [communityParsed, setCommunityParsed] = useState<ReturnType<
    typeof parseCommunity
  > | null>(null);
  const [directionsParsed, setDirectionsParsed] = useState<ReturnType<
    typeof parseDirections
  > | null>(null);
  const [draftParsed, setDraftParsed] = useState<ReturnType<
    typeof parseDraft
  > | null>(null);

  const steps = useMemo(
    () => [
      {
        key: "critique",
        title: "Critique & Score",
        desc: "Assess clarity, novelty, feasibility; assign a score",
      },
      {
        key: "literature",
        title: "Literature Review",
        desc: "Find related papers, datasets, figures",
      },
      {
        key: "forums",
        title: "Community Trends",
        desc: "Scan forums for gaps & trending questions",
      },
      {
        key: "direction",
        title: "Directions & Resources",
        desc: "Recommend research directions with sources",
      },
      {
        key: "draft",
        title: "Draft Outline",
        desc: "Create a paper outline with sections",
      },
    ],
    [],
  );

  /* ---------- animated bg ---------- */
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const particlesRef = useRef<
    { x: number; y: number; vx: number; vy: number }[]
  >([]);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d")!;
    let w = (canvas.width = window.innerWidth);
    let h = (canvas.height = window.innerHeight);

    const resize = () => {
      w = canvas.width = window.innerWidth;
      h = canvas.height = window.innerHeight;
    };
    window.addEventListener("resize", resize);

    const P = 90;
    if (particlesRef.current.length === 0) {
      particlesRef.current = Array.from({ length: P }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.6,
        vy: (Math.random() - 0.5) * 0.6,
      }));
    }

    const loop = () => {
      ctx.clearRect(0, 0, w, h);

      // Better theme-aware gradient
      const centerColor =
        theme === "dark" ? "rgba(66,153,225,0.15)" : "rgba(99,102,241,0.08)";
      const edgeColor =
        theme === "dark" ? "rgba(0,0,0,0)" : "rgba(255,255,255,0)";

      const g = ctx.createRadialGradient(
        w * 0.5,
        h * 0.4,
        0,
        w * 0.5,
        h * 0.4,
        Math.max(w, h) * 0.8,
      );
      g.addColorStop(0, centerColor);
      g.addColorStop(1, edgeColor);
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, w, h);

      const dotColor =
        theme === "dark"
          ? "rgba(173, 216, 230, 0.8)"
          : "rgba(99, 102, 241, 0.4)";
      const lineColor =
        theme === "dark"
          ? "rgba(100, 180, 255, 0.08)"
          : "rgba(99, 102, 241, 0.12)";

      const pts = particlesRef.current;
      for (let i = 0; i < pts.length; i++) {
        const p = pts[i];
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > w) p.vx *= -1;
        if (p.y < 0 || p.y > h) p.vy *= -1;

        ctx.beginPath();
        ctx.arc(p.x, p.y, 1.4, 0, Math.PI * 2);
        ctx.fillStyle = dotColor;
        ctx.fill();

        for (let j = i + 1; j < pts.length; j++) {
          const q = pts[j];
          const dx = p.x - q.x;
          const dy = p.y - q.y;
          const d2 = dx * dx + dy * dy;
          if (d2 < 130 * 130) {
            ctx.strokeStyle = lineColor;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(q.x, q.y);
            ctx.stroke();
          }
        }
      }
      rafRef.current = requestAnimationFrame(loop);
    };
    loop();

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      window.removeEventListener("resize", resize);
    };
  }, [theme]); // Fixed dependency

  /* ---------- misc handlers ---------- */
  const pushToast = (t: string) => {
    setToasts((prev) => [...prev, t]);
    setTimeout(() => setToasts((prev) => prev.slice(1)), 2500);
  };

  const handleFiles = (fileList: FileList | null) => {
    if (!fileList) return;
    const arr: FileInfo[] = [];
    Array.from(fileList).forEach((f) => {
      const info: FileInfo = { name: f.name, size: f.size, type: f.type };
      if (f.type.startsWith("image/")) info.url = URL.createObjectURL(f);
      arr.push(info);
    });
    setFiles((prev) => [...prev, ...arr]);
    pushToast(`${arr.length} file${arr.length > 1 ? "s" : ""} added`);
  };

  const startFlow = async () => {
    if (!idea.trim()) return pushToast("Type your research idea first");
    setSubmitted(true);
    setChatOpen(true);
    setRunning(true);
    setActiveStep(0);
    setMessages((m) => [...m, { role: "user", text: idea.trim() }]);

    try {
      // ---- STEP 1: Critique ----
      setActiveStep(0);
      setMessages((m) => [
        ...m,
        { role: "agent", text: "Critique & Score: Assessing idea..." },
      ]);

      const resCrit = await fetch(`${API_BASE}/api/critique`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idea }),
      });
      if (!resCrit.ok) throw new Error("Critique failed");
      const crit = await resCrit.json();
      const parsedCrit = parseCritique(JSON.stringify(crit));
      setCritiqueParsed(parsedCrit);
      setCritiqueScore(parsedCrit?.scores?.overall ?? null);

      // ---- STEP 2: Literature ----
      setActiveStep(1);
      setMessages((m) => [
        ...m,
        { role: "agent", text: "Literature Review: Gathering resources..." },
      ]);

      const resLit = await fetch(`${API_BASE}/api/literature`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idea }),
      });
      if (!resLit.ok) throw new Error("Literature failed");
      const lit = await resLit.json();
      setLitParsed(parseLiterature(JSON.stringify(lit)));

      // ---- STEP 3: Community Trends ----
      setActiveStep(2);
      setMessages((m) => [
        ...m,
        {
          role: "agent",
          text: "Community Trends: Scanning forums & discussions...",
        },
      ]);

      const resCom = await fetch(`${API_BASE}/api/community`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idea }),
      });
      if (!resCom.ok) throw new Error("Community scan failed");
      const com = await resCom.json();
      setCommunityParsed(parseCommunity(JSON.stringify(com)));

      // ---- STEP 4: Directions & Resources ----
      setActiveStep(3);
      setMessages((m) => [
        ...m,
        {
          role: "agent",
          text: "Directions & Resources: Converging on what to build next...",
        },
      ]);

      const resDir = await fetch(`${API_BASE}/api/directions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idea }),
      });
      if (!resDir.ok) throw new Error("Directions failed");
      const dir = await resDir.json();
      setDirectionsParsed(parseDirections(JSON.stringify(dir)));

      // ---- STEP 5: Draft Outline ----
      setActiveStep(4);
      setMessages((m) => [
        ...m,
        {
          role: "agent",
          text: "Draft Outline: Generating a structured paper outline...",
        },
      ]);

      const resDraft = await fetch(`${API_BASE}/api/draft`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idea }),
      });
      if (!resDraft.ok) throw new Error("Draft outline failed");
      const draft = await resDraft.json();
      setDraftParsed(parseDraft(JSON.stringify(draft)));

      // done
      setRunning(false);
    } catch (err: any) {
      pushToast(err?.message || "Something went wrong");
      setRunning(false);
    }
  };

  const exportDraft = () => {
    const data = {
      idea,
      model,
      files: files.map(({ name, size, type }) => ({ name, size, type })),
      chat: messages,
      timestamp: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `gd_research_${Date.now()}.json`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 500);
    pushToast("Draft exported");
  };

  const resetFlow = () => {
    setSubmitted(false);
    setRunning(false);
    setActiveStep(-1);
    setMessages([]);
    setIdea("");
    setFiles([]);
    setCritiqueScore(null);
    setCritiqueParsed(null);
    setLitParsed(null);
    pushToast("Reset complete");
  };

  useShortcuts({
    analyze: startFlow,
    reset: resetFlow,
    openChat: () => setChatOpen((v) => !v),
    exportDraft,
  });

  /* -------------------- UI -------------------- */
  return (
    <div
      className={cx(
        "min-h-screen bg-neutral-950 text-neutral-100",
        "min-h-screen bg-gray-50 text-gray-900",
        theme,
      )}
    >
      {/* background */}
      <canvas ref={canvasRef} className="pointer-events-none fixed inset-0" />

      {/* Toasts */}
      <div className="pointer-events-none fixed top-4 left-1/2 -translate-x-1/2 z-50 flex flex-col gap-2 items-center">
        <AnimatePresence>
          {toasts.map((t, i) => (
            <motion.div
              key={i}
              initial={{ y: -10, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <Toast text={t} theme={theme} />
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Header */}
      <header className="relative z-10 flex items-center justify-between px-6 md:px-10 py-4">
        <div className="flex items-center gap-3">
          <div
            className={cx(
              "h-8 w-8 rounded-xl bg-sky-500/20 ring-1 ring-sky-400/30 grid place-items-center",
              "h-8 w-8 rounded-xl bg-indigo-500/15 ring-1 ring-indigo-400/30 grid place-items-center",
              theme,
            )}
          >
            🧬
          </div>
          <span className="font-semibold tracking-tight">GD Research Lab</span>
          <span
            className={cx(
              "ml-2 text-[10px] px-2 py-0.5 rounded-full bg-white/5 border border-white/10",
              "ml-2 text-[10px] px-2 py-0.5 rounded-full bg-black/5 border border-black/10",
              theme,
            )}
          >
            beta
          </span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          {/* <select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className={cx(
              "bg-neutral-900 text-white border border-neutral-700 rounded-lg px-2 py-1",
              "bg-white text-gray-900 border border-gray-300 rounded-lg px-2 py-1",
              theme
            )}
          >
            <option value="Gemini 1.5 Flash">Gemini 1.5 Flash</option>
            <option value="Gemini 1.5 Pro">Gemini 1.5 Pro</option>
            <option value="GPT-4o mini">GPT-4o mini</option>
          </select> */}
          <button
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className={cx(
              "ml-2 rounded-xl border border-neutral-700 px-3 py-1.5 hover:bg-neutral-800 transition-colors",
              "ml-2 rounded-xl border border-gray-300 px-3 py-1.5 hover:bg-gray-100 transition-colors",
              theme,
            )}
          >
            {theme === "dark" ? "☀️ Light" : "🌙 Dark"}
          </button>
        </div>
      </header>

      {/* Main */}
      <main className="relative z-10 mx-auto max-w-[100vw] px-6 md:px-10 pb-28">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[calc(100vh-200px)]">
          {/* left column */}
          <div className="lg:col-span-8 flex flex-col">
            <AnimatePresence mode="wait">
              {!submitted ? (
                /* ---- HERO / INPUT ---- */
                <motion.section
                  key="hero"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.5 }}
                  className="mt-6 flex-1 flex flex-col justify-center"
                >
                  <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight text-center md:text-left">
                    Build better{" "}
                    <span
                      className={cx("text-blue-400", "text-indigo-600", theme)}
                    >
                      research
                    </span>{" "}
                    faster
                  </h1>
                  <p
                    className={cx(
                      "mt-4 text-neutral-300 text-lg max-w-2xl",
                      "mt-4 text-gray-600 text-lg max-w-2xl",
                      theme,
                    )}
                  >
                    An AI mentor that{" "}
                    <span
                      className={cx(
                        "text-white font-semibold",
                        "text-gray-900 font-semibold",
                        theme,
                      )}
                    >
                      critiques ideas
                    </span>
                    , finds gaps, and charts your next steps.
                  </p>

                  <div
                    className={cx(
                      "mt-6 rounded-3xl bg-neutral-900/70 border border-neutral-800 p-6 shadow-2xl backdrop-blur",
                      "mt-6 rounded-3xl bg-white border border-gray-200 p-6 shadow-lg",
                      theme,
                    )}
                  >
                    <label
                      className={cx(
                        "block text-sm text-neutral-400 mb-2",
                        "block text-sm text-gray-500 mb-2",
                        theme,
                      )}
                    >
                      Enter your research idea
                    </label>
                    <textarea
                      value={idea}
                      onChange={(e) => setIdea(e.target.value)}
                      rows={5}
                      placeholder="e.g., AI to detect diabetic retinopathy in smartphone fundus images for rural clinics"
                      className={cx(
                        "w-full resize-none rounded-2xl bg-neutral-950/70 border border-neutral-800 px-4 py-3 outline-none focus:ring-2 focus:ring-sky-500/50 text-white placeholder-neutral-500",
                        "w-full resize-none rounded-2xl bg-white border border-gray-300 px-4 py-3 outline-none focus:ring-2 focus:ring-indigo-500/30 text-gray-900 placeholder-gray-500",
                        theme,
                      )}
                    />

                    {/* Dropzone */}
                    <div
                      className={cx(
                        "mt-4 rounded-2xl border border-dashed border-neutral-700 p-4 text-sm text-neutral-400 hover:border-sky-500/50 transition cursor-pointer",
                        "mt-4 rounded-2xl border border-dashed border-gray-300 p-4 text-sm text-gray-500 hover:border-indigo-400/50 transition cursor-pointer",
                        theme,
                      )}
                      onDragOver={(e) => e.preventDefault()}
                      onDrop={(e) => {
                        e.preventDefault();
                        handleFiles(e.dataTransfer.files);
                      }}
                      onClick={() =>
                        document.getElementById("file-input")?.click()
                      }
                    >
                      <input
                        id="file-input"
                        type="file"
                        className="hidden"
                        multiple
                        onChange={(e) => handleFiles(e.target.files)}
                      />
                      <div className="flex items-center gap-2">
                        <span>📎</span>
                        <span>Drop PDFs/images here or click to upload</span>
                      </div>
                      {files.length > 0 && (
                        <div className="mt-3 grid grid-cols-2 md:grid-cols-3 gap-2">
                          {files.map((f, i) => (
                            <div
                              key={i}
                              className={cx(
                                "rounded-xl border border-neutral-800 bg-neutral-950/60 p-2 text-xs",
                                "rounded-xl border border-gray-200 bg-gray-50 p-2 text-xs",
                                theme,
                              )}
                            >
                              <div className="truncate">{f.name}</div>
                              <div
                                className={cx(
                                  "text-neutral-500",
                                  "text-gray-500",
                                  theme,
                                )}
                              >
                                {(f.size / 1024 / 1024).toFixed(2)} MB
                              </div>
                              {f.url && (
                                <img
                                  src={f.url}
                                  alt="preview"
                                  className="mt-1 rounded-lg max-h-24 object-cover"
                                />
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>


                    <div className="mt-4 flex flex-wrap items-center gap-3">
                      <input
                        id="audio-input"
                        type="file"
                        accept="audio/*"
                        className="hidden"
                        onChange={async (e) => {
                          const f = e.target.files?.[0];
                          if (!f) return;
                          try {
                            pushToast("Uploading audio…");
                            const url = await sttUpload(f);
                            pushToast("Starting transcription…");
                            const tid = await sttStart(url);
                            const text = await sttPoll(tid, (s) => {
                              // optional: show status
                            });
                            // append the transcribed text to the idea box (or open a dialog)
                            setIdea((prev) => (prev ? prev + "\n\n" + text : text));
                            pushToast("Transcription complete");
                          } catch (err: any) {
                            pushToast(err?.message || "STT failed");
                          } finally {
                            // reset input so the same file can be re-selected
                            (document.getElementById("audio-input") as HTMLInputElement).value = "";
                          }
                        }}
                      />
                      <button
                        onClick={() => document.getElementById("audio-input")?.click()}
                        className={cx(
                          "rounded-2xl border border-neutral-700 hover:bg-neutral-800 transition px-4 py-2.5",
                          "rounded-2xl border border-gray-300 hover:bg-gray-100 transition px-4 py-2.5",
                          theme,
                        )}
                      >
                        🎙️ Add Audio
                      </button>
                    </div>


                    <div className="mt-4 flex flex-wrap items-center gap-3">
                      <button
                        onClick={startFlow}
                        className={cx(
                          "rounded-2xl bg-sky-600 hover:bg-sky-500 transition px-4 py-2.5 font-medium shadow-lg text-white",
                          "rounded-2xl bg-indigo-600 hover:bg-indigo-500 transition px-4 py-2.5 font-medium text-white shadow-lg",
                          theme,
                        )}
                      >
                        Analyze Idea
                      </button>
                      <button
                        onClick={() => setIdea("")}
                        className={cx(
                          "rounded-2xl border border-neutral-700 hover:bg-neutral-800 transition px-4 py-2.5",
                          "rounded-2xl border border-gray-300 hover:bg-gray-100 transition px-4 py-2.5",
                          theme,
                        )}
                      >
                        Clear
                      </button>

                    </div>
                  </div>
                </motion.section>
              ) : (
                /* ---- PIPELINE ---- */
                <motion.section
                  key="pipeline"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.5 }}
                  className="mt-4 flex-1"
                >
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h2 className="text-2xl font-semibold">
                        Multi-Agent Workflow
                      </h2>
                      <p
                        className={cx(
                          "text-sm text-neutral-400 mt-1",
                          "text-sm text-gray-600 mt-1",
                          theme,
                        )}
                      >
                        Creating a comprehensive research analysis with multiple
                        AI agents
                      </p>
                    </div>
                    {/* {critiqueScore != null && <Gauge value={critiqueScore} theme={theme} />} */}
                  </div>

                  <div className="space-y-4">
                    {steps.map((step, idx) => {
                      const isActive = idx === activeStep;
                      const isDone =
                        idx < activeStep ||
                        (!running && activeStep === steps.length - 1);

                      const cardBase = cx(
                        "border-neutral-800 bg-neutral-900/60 hover:bg-neutral-900/70",
                        "border-gray-200 bg-white hover:bg-gray-50",
                        theme,
                      );
                      const doneBase = cx(
                        "border-emerald-500/30 bg-emerald-500/5",
                        "border-emerald-300 bg-emerald-50",
                        theme,
                      );
                      const activeBase = cx(
                        "border-sky-500/40 bg-sky-500/5",
                        "border-indigo-300 bg-indigo-50",
                        theme,
                      );

                      return (
                        <motion.div
                          layout
                          key={step.key}
                          className={`rounded-2xl border p-4 backdrop-blur shadow-sm transition-all duration-200 ${
                            isDone ? doneBase : isActive ? activeBase : cardBase
                          }`}
                        >
                          {/* step header */}
                          <div className="flex items-start gap-3">
                            <div
                              className={`h-8 w-8 rounded-xl grid place-items-center text-sm font-medium ${
                                isDone
                                  ? cx(
                                      "bg-emerald-500/20 text-emerald-400",
                                      "bg-emerald-100 text-emerald-700",
                                      theme,
                                    )
                                  : isActive
                                    ? cx(
                                        "bg-sky-500/20 text-sky-400",
                                        "bg-indigo-100 text-indigo-700",
                                        theme,
                                      )
                                    : cx(
                                        "bg-neutral-800 text-neutral-400",
                                        "bg-gray-200 text-gray-600",
                                        theme,
                                      )
                              }`}
                            >
                              {isDone ? "✓" : isActive ? "⟳" : idx + 1}
                            </div>

                            <div className="flex-1">
                              <div className="font-medium flex items-center justify-between">
                                <span
                                  className={cx(
                                    "text-neutral-100",
                                    "text-gray-900",
                                    theme,
                                  )}
                                >
                                  {step.title}
                                </span>
                                {isActive && (
                                  <span
                                    className={cx(
                                      "text-[10px] px-2 py-0.5 rounded-full border border-sky-500/30 text-sky-300 bg-sky-500/5",
                                      "text-[10px] px-2 py-0.5 rounded-full border border-indigo-300 text-indigo-700 bg-indigo-50",
                                      theme,
                                    )}
                                  >
                                    running...
                                  </span>
                                )}
                              </div>
                              <div
                                className={cx(
                                  "text-sm text-neutral-400 mt-1",
                                  "text-sm text-gray-600 mt-1",
                                  theme,
                                )}
                              >
                                {step.desc}
                              </div>

                              {isActive && (
                                <div
                                  className={cx(
                                    "mt-3 h-1.5 w-full overflow-hidden rounded-full bg-neutral-800/50",
                                    "mt-3 h-1.5 w-full overflow-hidden rounded-full bg-gray-200",
                                    theme,
                                  )}
                                >
                                  <motion.div
                                    className={cx(
                                      "h-full bg-sky-500/70",
                                      "h-full bg-indigo-500",
                                      theme,
                                    )}
                                    initial={{ width: 0 }}
                                    animate={{ width: "100%" }}
                                    transition={{
                                      duration: 1.1,
                                      ease: "easeInOut",
                                    }}
                                  />
                                </div>
                              )}
                            </div>
                          </div>

                          {/* --- CRITIQUE PANEL --- */}
                          {step.key === "critique" &&
                            (isDone || isActive) &&
                            critiqueParsed && (
                              <div className="mt-4 space-y-4">
                                {critiqueParsed.meta?.title && (
                                  <SectionCard
                                    title="Research Idea Analysis"
                                    theme={theme}
                                  >
                                    <div className="space-y-2">
                                      <div className="font-semibold">
                                        {critiqueParsed.meta.title}
                                      </div>
                                      {critiqueParsed.meta.domain && (
                                        <div
                                          className={cx(
                                            "text-xs text-neutral-500",
                                            "text-xs text-gray-500",
                                            theme,
                                          )}
                                        >
                                          Domain: {critiqueParsed.meta.domain}
                                        </div>
                                      )}
                                      {critiqueParsed.meta.description && (
                                        <p
                                          className={cx(
                                            "text-sm text-neutral-300",
                                            "text-sm text-gray-700",
                                            theme,
                                          )}
                                        >
                                          {critiqueParsed.meta.description}
                                        </p>
                                      )}
                                    </div>
                                  </SectionCard>
                                )}

                                <div
                                  className={cx(
                                    "rounded-2xl border border-neutral-800 bg-black/20 p-4",
                                    "rounded-2xl border border-gray-200 bg-white p-4",
                                    theme,
                                  )}
                                >
                                  <h4
                                    className={cx(
                                      "font-medium mb-3 text-neutral-100",
                                      "font-medium mb-3 text-gray-900",
                                      theme,
                                    )}
                                  >
                                    Scoring Breakdown
                                  </h4>
                                  <div className="grid md:grid-cols-2 gap-6">
                                    <div className="space-y-3 text-sm">
                                      <div className="flex items-center gap-3">
                                        <div
                                          className={cx(
                                            "w-20 text-neutral-400",
                                            "w-20 text-gray-600",
                                            theme,
                                          )}
                                        >
                                          Novelty
                                        </div>
                                        <ProgressBar
                                          value={
                                            critiqueParsed.scores?.novelty ?? 0
                                          }
                                          theme={theme}
                                        />
                                        <div
                                          className={cx(
                                            "w-8 text-right font-medium",
                                            "w-8 text-right font-medium",
                                            theme,
                                          )}
                                        >
                                          {critiqueParsed.scores?.novelty ??
                                            "—"}
                                        </div>
                                      </div>
                                      <div className="flex items-center gap-3">
                                        <div
                                          className={cx(
                                            "w-20 text-neutral-400",
                                            "w-20 text-gray-600",
                                            theme,
                                          )}
                                        >
                                          Feasibility
                                        </div>
                                        <ProgressBar
                                          value={
                                            critiqueParsed.scores
                                              ?.feasibility ?? 0
                                          }
                                          theme={theme}
                                        />
                                        <div
                                          className={cx(
                                            "w-8 text-right font-medium",
                                            "w-8 text-right font-medium",
                                            theme,
                                          )}
                                        >
                                          {critiqueParsed.scores?.feasibility ??
                                            "—"}
                                        </div>
                                      </div>
                                      <div className="flex items-center gap-3">
                                        <div
                                          className={cx(
                                            "w-20 text-neutral-400",
                                            "w-20 text-gray-600",
                                            theme,
                                          )}
                                        >
                                          Impact
                                        </div>
                                        <ProgressBar
                                          value={
                                            critiqueParsed.scores?.impact ?? 0
                                          }
                                          theme={theme}
                                        />
                                        <div
                                          className={cx(
                                            "w-8 text-right font-medium",
                                            "w-8 text-right font-medium",
                                            theme,
                                          )}
                                        >
                                          {critiqueParsed.scores?.impact ?? "—"}
                                        </div>
                                      </div>
                                    </div>
                                    <div className="flex items-center justify-center">
                                      <Gauge
                                        value={
                                          critiqueParsed.scores?.overall ?? 0
                                        }
                                        theme={theme}
                                      />
                                    </div>
                                  </div>
                                </div>

                                {(critiqueParsed.reasons?.noveltyReason ||
                                  critiqueParsed.reasons?.feasibilityReason ||
                                  critiqueParsed.reasons?.impactReason) && (
                                  <SectionCard
                                    title="Detailed Analysis"
                                    theme={theme}
                                  >
                                    <div
                                      className={cx(
                                        "space-y-3 text-sm text-neutral-300",
                                        "space-y-3 text-sm text-gray-700",
                                        theme,
                                      )}
                                    >
                                      {critiqueParsed.reasons
                                        ?.noveltyReason && (
                                        <div>
                                          <span className="font-semibold text-sky-400">
                                            Novelty:
                                          </span>{" "}
                                          {critiqueParsed.reasons.noveltyReason}
                                        </div>
                                      )}
                                      {critiqueParsed.reasons
                                        ?.feasibilityReason && (
                                        <div>
                                          <span className="font-semibold text-orange-400">
                                            Feasibility:
                                          </span>{" "}
                                          {
                                            critiqueParsed.reasons
                                              .feasibilityReason
                                          }
                                        </div>
                                      )}
                                      {critiqueParsed.reasons?.impactReason && (
                                        <div>
                                          <span className="font-semibold text-green-400">
                                            Impact:
                                          </span>{" "}
                                          {critiqueParsed.reasons.impactReason}
                                        </div>
                                      )}
                                    </div>
                                  </SectionCard>
                                )}

                                {critiqueParsed.gaps?.length > 0 && (
                                  <SectionCard
                                    title="Identified Gaps"
                                    theme={theme}
                                  >
                                    <Chips
                                      items={critiqueParsed.gaps}
                                      tone="warn"
                                      theme={theme}
                                    />
                                  </SectionCard>
                                )}

                                {critiqueParsed.suggestions?.length > 0 && (
                                  <SectionCard
                                    title="Recommendations"
                                    theme={theme}
                                  >
                                    <div
                                      className={cx(
                                        "space-y-2 text-sm text-neutral-300",
                                        "space-y-2 text-sm text-gray-700",
                                        theme,
                                      )}
                                    >
                                      {critiqueParsed.suggestions.map(
                                        (sug, i) => (
                                          <div
                                            key={i}
                                            className="flex items-start gap-2"
                                          >
                                            <span
                                              className={cx(
                                                "text-sky-400 mt-0.5",
                                                "text-indigo-500 mt-0.5",
                                                theme,
                                              )}
                                            >
                                              •
                                            </span>
                                            <span>{sug}</span>
                                          </div>
                                        ),
                                      )}
                                    </div>
                                  </SectionCard>
                                )}

                                {critiqueParsed.verdict && (
                                  <div
                                    className={cx(
                                      "rounded-2xl border border-yellow-500/20 bg-yellow-500/5 p-4 text-sm text-yellow-300",
                                      "rounded-2xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-800",
                                      theme,
                                    )}
                                  >
                                    <div className="font-semibold mb-2">
                                      Overall Assessment
                                    </div>
                                    {critiqueParsed.verdict}
                                  </div>
                                )}
                              </div>
                            )}

                          {/* --- LITERATURE PANEL --- */}
                          {step.key === "literature" &&
                            (isDone || isActive) &&
                            litParsed && (
                              <div className="mt-4 space-y-4">
                                {litParsed.meta?.title && (
                                  <SectionCard
                                    title="Literature Overview"
                                    theme={theme}
                                  >
                                    <div className="space-y-2">
                                      <div className="font-semibold">
                                        {litParsed.meta.title}
                                      </div>
                                      {litParsed.meta.domain && (
                                        <div
                                          className={cx(
                                            "text-xs text-neutral-500",
                                            "text-xs text-gray-500",
                                            theme,
                                          )}
                                        >
                                          Domain: {litParsed.meta.domain}
                                        </div>
                                      )}
                                      {litParsed.meta.description && (
                                        <p
                                          className={cx(
                                            "text-sm text-neutral-300",
                                            "text-sm text-gray-700",
                                            theme,
                                          )}
                                        >
                                          {litParsed.meta.description}
                                        </p>
                                      )}
                                    </div>
                                  </SectionCard>
                                )}

                                {litParsed.research_questions?.length > 0 && (
                                  <SectionCard
                                    title="Key Research Questions"
                                    theme={theme}
                                  >
                                    <DotList
                                      items={litParsed.research_questions}
                                      theme={theme}
                                    />
                                  </SectionCard>
                                )}

                                <div className="grid md:grid-cols-2 gap-4">
                                  {litParsed.niches?.length > 0 && (
                                    <SectionCard
                                      title="Research Niches"
                                      theme={theme}
                                    >
                                      <Chips
                                        items={litParsed.niches}
                                        theme={theme}
                                      />
                                    </SectionCard>
                                  )}

                                  {litParsed.methodologies?.length > 0 && (
                                    <SectionCard
                                      title="Common Methodologies"
                                      theme={theme}
                                    >
                                      <DotList
                                        items={litParsed.methodologies}
                                        theme={theme}
                                      />
                                    </SectionCard>
                                  )}

                                  {litParsed.trends?.length > 0 && (
                                    <SectionCard
                                      title="Current Trends"
                                      theme={theme}
                                    >
                                      <DotList
                                        items={litParsed.trends}
                                        theme={theme}
                                      />
                                    </SectionCard>
                                  )}

                                  {litParsed.major_gaps?.length > 0 && (
                                    <SectionCard
                                      title="Research Gaps"
                                      theme={theme}
                                    >
                                      <Chips
                                        items={litParsed.major_gaps}
                                        tone="warn"
                                        theme={theme}
                                      />
                                    </SectionCard>
                                  )}

                                  {litParsed.emerging_trends?.length > 0 && (
                                    <SectionCard
                                      title="Emerging Trends"
                                      theme={theme}
                                    >
                                      <DotList
                                        items={litParsed.emerging_trends}
                                        theme={theme}
                                      />
                                    </SectionCard>
                                  )}

                                  {litParsed.opportunities?.length > 0 && (
                                    <SectionCard
                                      title="Opportunities"
                                      theme={theme}
                                    >
                                      <DotList
                                        items={litParsed.opportunities}
                                        theme={theme}
                                      />
                                    </SectionCard>
                                  )}
                                </div>

                                {(litParsed.key_papers?.length > 0 ||
                                  litParsed.datasets?.length > 0) && (
                                  <div className="grid md:grid-cols-2 gap-4">
                                    {litParsed.key_papers?.length > 0 && (
                                      <SectionCard
                                        title="Key Papers"
                                        theme={theme}
                                      >
                                        <div className="space-y-3">
                                          {litParsed.key_papers.map(
                                            (paper: any, i: number) => (
                                              <div
                                                key={i}
                                                className={cx(
                                                  "rounded-lg border border-neutral-800 bg-neutral-950/60 p-3",
                                                  "rounded-lg border border-gray-200 bg-gray-50 p-3",
                                                  theme,
                                                )}
                                              >
                                                <div className="font-medium text-sm mb-1">
                                                  {paper.title}
                                                </div>
                                                <div
                                                  className={cx(
                                                    "text-xs text-neutral-500",
                                                    "text-xs text-gray-500",
                                                    theme,
                                                  )}
                                                >
                                                  {paper.venue}
                                                  {paper.year
                                                    ? ` • ${paper.year}`
                                                    : ""}
                                                </div>
                                                {paper.link && (
                                                  <a
                                                    className={cx(
                                                      "text-xs text-sky-300 hover:underline",
                                                      "text-xs text-indigo-600 hover:underline",
                                                      theme,
                                                    )}
                                                    href={paper.link}
                                                  >
                                                    View Paper →
                                                  </a>
                                                )}
                                              </div>
                                            ),
                                          )}
                                        </div>
                                      </SectionCard>
                                    )}

                                    {litParsed.datasets?.length > 0 && (
                                      <SectionCard
                                        title="Relevant Datasets"
                                        theme={theme}
                                      >
                                        <div className="space-y-3">
                                          {litParsed.datasets.map(
                                            (dataset: any, i: number) => (
                                              <div
                                                key={i}
                                                className={cx(
                                                  "rounded-lg border border-neutral-800 bg-neutral-950/60 p-3",
                                                  "rounded-lg border border-gray-200 bg-gray-50 p-3",
                                                  theme,
                                                )}
                                              >
                                                <div className="font-medium text-sm mb-1">
                                                  {dataset.name}
                                                </div>
                                                {dataset.size && (
                                                  <div
                                                    className={cx(
                                                      "text-xs text-neutral-500",
                                                      "text-xs text-gray-500",
                                                      theme,
                                                    )}
                                                  >
                                                    {dataset.size}
                                                  </div>
                                                )}
                                                {dataset.link && (
                                                  <a
                                                    className={cx(
                                                      "text-xs text-sky-300 hover:underline",
                                                      "text-xs text-indigo-600 hover:underline",
                                                      theme,
                                                    )}
                                                    href={dataset.link}
                                                  >
                                                    Access Dataset →
                                                  </a>
                                                )}
                                              </div>
                                            ),
                                          )}
                                        </div>
                                      </SectionCard>
                                    )}
                                  </div>
                                )}

                                {(litParsed.tools?.length > 0 ||
                                  litParsed.venues?.length > 0) && (
                                  <div className="grid md:grid-cols-2 gap-4">
                                    {litParsed.tools?.length > 0 && (
                                      <SectionCard
                                        title="Common Tools & Frameworks"
                                        theme={theme}
                                      >
                                        <Chips
                                          items={litParsed.tools}
                                          theme={theme}
                                        />
                                      </SectionCard>
                                    )}

                                    {litParsed.venues?.length > 0 && (
                                      <SectionCard
                                        title="Publication Venues"
                                        theme={theme}
                                      >
                                        <Chips
                                          items={litParsed.venues}
                                          theme={theme}
                                        />
                                      </SectionCard>
                                    )}
                                  </div>
                                )}
                              </div>
                            )}

                          {/* --- COMMUNITY PANEL (Step 3) --- */}
                          {step.key === "forums" &&
                            (isDone || isActive) &&
                            communityParsed && (
                              <div className="mt-4 space-y-4">
                                {communityParsed.trends?.length > 0 && (
                                  <SectionCard
                                    title="Top Community Trends"
                                    theme={theme}
                                  >
                                    <DotList
                                      items={communityParsed.trends}
                                      theme={theme}
                                    />
                                  </SectionCard>
                                )}
                                {communityParsed.threads?.reddit?.length ||
                                communityParsed.threads?.medium?.length ||
                                communityParsed.threads?.quora?.length ? (
                                  <div className="grid md:grid-cols-2 gap-4">
                                    {communityParsed.threads?.reddit?.length >
                                      0 && (
                                      <SectionCard
                                        title="Reddit Threads"
                                        theme={theme}
                                      >
                                        <div className="space-y-2 text-sm">
                                          {communityParsed.threads.reddit.map(
                                            (t: any, i: number) => (
                                              <div key={i} className="truncate">
                                                <a
                                                  className={cx(
                                                    "text-sky-300 hover:underline",
                                                    "text-indigo-600 hover:underline",
                                                    theme,
                                                  )}
                                                  href={t.link}
                                                  target="_blank"
                                                >
                                                  {t.title || "Post"}
                                                </a>
                                              </div>
                                            ),
                                          )}
                                        </div>
                                      </SectionCard>
                                    )}
                                    {communityParsed.threads?.medium?.length >
                                      0 && (
                                      <SectionCard
                                        title="Medium Posts"
                                        theme={theme}
                                      >
                                        <div className="space-y-2 text-sm">
                                          {communityParsed.threads.medium.map(
                                            (t: any, i: number) => (
                                              <div key={i} className="truncate">
                                                <a
                                                  className={cx(
                                                    "text-sky-300 hover:underline",
                                                    "text-indigo-600 hover:underline",
                                                    theme,
                                                  )}
                                                  href={t.link}
                                                  target="_blank"
                                                >
                                                  {t.title || "Article"}
                                                </a>
                                              </div>
                                            ),
                                          )}
                                        </div>
                                      </SectionCard>
                                    )}
                                    {communityParsed.threads?.quora?.length >
                                      0 && (
                                      <SectionCard
                                        title="Quora Q&A"
                                        theme={theme}
                                      >
                                        <div className="space-y-2 text-sm">
                                          {communityParsed.threads.quora.map(
                                            (t: any, i: number) => (
                                              <div key={i} className="truncate">
                                                <a
                                                  className={cx(
                                                    "text-sky-300 hover:underline",
                                                    "text-indigo-600 hover:underline",
                                                    theme,
                                                  )}
                                                  href={t.link}
                                                  target="_blank"
                                                >
                                                  {t.title || "Question"}
                                                </a>
                                              </div>
                                            ),
                                          )}
                                        </div>
                                      </SectionCard>
                                    )}
                                  </div>
                                ) : null}
                              </div>
                            )}

                          {/* --- DIRECTIONS PANEL (Step 4) --- */}
                          {step.key === "direction" &&
                            (isDone || isActive) &&
                            directionsParsed && (
                              <div className="mt-4 space-y-4">
                                {directionsParsed.summary && (
                                  <SectionCard title="Summary" theme={theme}>
                                    <p
                                      className={cx(
                                        "text-sm text-neutral-300",
                                        "text-sm text-gray-700",
                                        theme,
                                      )}
                                    >
                                      {directionsParsed.summary}
                                    </p>
                                  </SectionCard>
                                )}
                                {directionsParsed.directions?.length > 0 && (
                                  <SectionCard
                                    title="Concrete Next Steps"
                                    theme={theme}
                                  >
                                    <DotList
                                      items={directionsParsed.directions}
                                      theme={theme}
                                    />
                                  </SectionCard>
                                )}
                                {directionsParsed.resources && (
                                  <div className="grid md:grid-cols-2 gap-4">
                                    {directionsParsed.resources.tools?.length >
                                      0 && (
                                      <SectionCard title="Tools" theme={theme}>
                                        <Chips
                                          items={
                                            directionsParsed.resources.tools
                                          }
                                          theme={theme}
                                        />
                                      </SectionCard>
                                    )}
                                    {directionsParsed.resources.checklists
                                      ?.length > 0 && (
                                      <SectionCard
                                        title="Checklists"
                                        theme={theme}
                                      >
                                        <DotList
                                          items={
                                            directionsParsed.resources
                                              .checklists
                                          }
                                          theme={theme}
                                        />
                                      </SectionCard>
                                    )}
                                    {directionsParsed.resources.datasets
                                      ?.length > 0 && (
                                      <SectionCard
                                        title="Datasets"
                                        theme={theme}
                                      >
                                        <div className="space-y-2 text-sm">
                                          {directionsParsed.resources.datasets.map(
                                            (d: any, i: number) => (
                                              <div key={i} className="truncate">
                                                <a
                                                  className={cx(
                                                    "text-sky-300 hover:underline",
                                                    "text-indigo-600 hover:underline",
                                                    theme,
                                                  )}
                                                  href={d.link}
                                                  target="_blank"
                                                >
                                                  {d.name || "Dataset"}
                                                </a>
                                              </div>
                                            ),
                                          )}
                                        </div>
                                      </SectionCard>
                                    )}
                                    {directionsParsed.resources.papers?.length >
                                      0 && (
                                      <SectionCard title="Papers" theme={theme}>
                                        <div className="space-y-2 text-sm">
                                          {directionsParsed.resources.papers.map(
                                            (p: any, i: number) => (
                                              <div key={i} className="truncate">
                                                <a
                                                  className={cx(
                                                    "text-sky-300 hover:underline",
                                                    "text-indigo-600 hover:underline",
                                                    theme,
                                                  )}
                                                  href={p.link}
                                                  target="_blank"
                                                >
                                                  {p.title || "Paper"}
                                                </a>
                                              </div>
                                            ),
                                          )}
                                        </div>
                                      </SectionCard>
                                    )}
                                  </div>
                                )}
                              </div>
                            )}

                          {/* --- DRAFT PANEL (Step 5) --- */}
                          {step.key === "draft" &&
                            (isDone || isActive) &&
                            draftParsed && (
                              <div className="mt-4 space-y-4">
                                {draftParsed.title && (
                                  <SectionCard
                                    title={draftParsed.title}
                                    theme={theme}
                                  >
                                    <div />
                                  </SectionCard>
                                )}
                                {draftParsed.outline?.length > 0 && (
                                  <div className="space-y-3">
                                    {draftParsed.outline.map(
                                      (sec: any, i: number) => (
                                        <SectionCard
                                          key={i}
                                          title={sec.section}
                                          theme={theme}
                                        >
                                          <DotList
                                            items={sec.bullets || []}
                                            theme={theme}
                                          />
                                        </SectionCard>
                                      ),
                                    )}
                                  </div>
                                )}
                              </div>
                            )}
                        </motion.div>
                      );
                    })}
                  </div>

                  <div className="mt-6 flex items-center gap-3 justify-center">
                    <button
                      className={cx(
                        "rounded-xl bg-neutral-800 hover:bg-neutral-700 border border-neutral-700 px-4 py-2 text-sm transition-colors",
                        "rounded-xl bg-white hover:bg-gray-100 border border-gray-300 px-4 py-2 text-sm transition-colors",
                        theme,
                      )}
                      onClick={resetFlow}
                    >
                      Start Over
                    </button>
                    <button
                      className={cx(
                        "rounded-xl bg-sky-600 hover:bg-sky-500 px-4 py-2 text-sm font-medium text-white shadow-lg transition-colors",
                        "rounded-xl bg-indigo-600 hover:bg-indigo-500 px-4 py-2 text-sm font-medium text-white shadow-lg transition-colors",
                        theme,
                      )}
                      onClick={exportDraft}
                    >
                      Export Results
                    </button>
                  </div>
                </motion.section>
              )}
            </AnimatePresence>
          </div>

          {/* right chat column (minimal + collapsible) */}
          <div className="lg:col-span-4">
            <AnimatePresence>
              {chatOpen && (
                <motion.aside
                  key="chat"
                  initial={{ opacity: 0, x: 40 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 40 }}
                  transition={{ duration: 0.45 }}
                  className={cx(
                    "sticky top-6 h-[calc(100vh-110px)] rounded-3xl border border-neutral-800 bg-neutral-900/70 backdrop-blur p-4 flex flex-col",
                    "sticky top-6 h-[calc(100vh-110px)] rounded-3xl border border-gray-200 bg-white p-4 flex flex-col shadow-sm",
                    theme,
                  )}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-semibold">Research Chat</div>
                    <button
                      onClick={() => setChatOpen(false)}
                      className={cx(
                        "text-neutral-400 hover:text-white text-sm",
                        "text-gray-500 hover:text-gray-900 text-sm",
                        theme,
                      )}
                    >
                      Collapse
                    </button>
                  </div>

                  <div className="flex-1 overflow-y-auto space-y-3 pr-1">
                    {messages.length === 0 && (
                      <p
                        className={cx(
                          "text-sm text-neutral-400",
                          "text-sm text-gray-500",
                          theme,
                        )}
                      >
                        Your conversation will appear here.
                      </p>
                    )}
                    {messages.map((m, i) => (
                      <div
                        key={i}
                        className={`group rounded-2xl px-3 py-2 text-sm max-w-[85%] ${
                          m.role === "user"
                            ? cx(
                                "ml-auto bg-sky-600/20 border border-sky-500/30",
                                "ml-auto bg-indigo-100 border border-indigo-200",
                                theme,
                              )
                            : cx(
                                "bg-neutral-800/80 border border-neutral-700",
                                "bg-gray-100 border border-gray-200",
                                theme,
                              )
                        }`}
                      >
                        <div className="flex items-start gap-2">
                          <div className="flex-1 whitespace-pre-wrap">
                            {m.text}
                          </div>
                          <button
                            className={cx(
                              "opacity-0 group-hover:opacity-100 text-xs text-neutral-400 hover:text-white",
                              "opacity-0 group-hover:opacity-100 text-xs text-gray-500 hover:text-gray-900",
                              theme,
                            )}
                            onClick={() => {
                              navigator.clipboard.writeText(m.text);
                              pushToast("Copied");
                            }}
                            title="Copy"
                          >
                            📋
                          </button>
                        </div>
                      </div>
                    ))}
                    {running && (
                      <div
                        className={cx(
                          "text-xs text-neutral-400",
                          "text-xs text-gray-500",
                          theme,
                        )}
                      >
                        Agent thinking…
                      </div>
                    )}
                  </div>

                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      const form = e.currentTarget as HTMLFormElement;
                      const data = new FormData(form);
                      const text = String(data.get("msg") || "").trim();
                      if (!text) return;
                      setMessages((m) => [...m, { role: "user", text }]);
                      (
                        form.elements.namedItem("msg") as HTMLInputElement
                      ).value = "";
                    }}
                    className="mt-3 flex items-center gap-2"
                  >
                    <input
                      name="msg"
                      placeholder="Ask to refine, add constraints, etc."
                      className={cx(
                        "flex-1 rounded-2xl bg-neutral-950/60 border border-neutral-800 px-3 py-2 outline-none focus:ring-2 focus:ring-sky-500/40",
                        "flex-1 rounded-2xl bg-white border border-gray-300 px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-500/30",
                        theme,
                      )}
                    />
                    <button
                      className={cx(
                        "rounded-2xl bg-sky-600 hover:bg-sky-500 px-3 py-2 text-sm font-medium",
                        "rounded-2xl bg-indigo-600 hover:bg-indigo-500 px-3 py-2 text-sm font-medium text-white",
                        theme,
                      )}
                    >
                      Send
                    </button>
                  </form>
                </motion.aside>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Floating bar */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="fixed bottom-6 right-6 z-40 flex gap-2"
        >
          <button
            onClick={() => setChatOpen((v) => !v)}
            className={cx(
              "rounded-full px-4 py-2 bg-white/10 border border-white/15 backdrop-blur hover:bg-white/15 text-sm",
              "rounded-full px-4 py-2 bg-white hover:bg-gray-100 border border-gray-300 text-sm",
              theme,
            )}
          >
            {chatOpen ? "Hide Chat" : "Chat"}
          </button>
          {/* <button
            onClick={exportDraft}
            className={cx("rounded-full px-4 py-2 bg-sky-600 hover:bg-sky-500 text-sm", "rounded-full px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-sm text-white", theme)}
          >
            Export
          </button> */}
          <button
            onClick={resetFlow}
            className={cx(
              "rounded-full px-4 py-2 bg-neutral-800 hover:bg-neutral-700 border border-neutral-700 text-sm",
              "rounded-full px-4 py-2 bg-white hover:bg-gray-100 border border-gray-300 text-sm",
              theme,
            )}
          >
            Reset
          </button>
        </motion.div>
      </main>

      {/* Footer */}
      <footer
        className={cx(
          "relative z-10 border-t border-neutral-900/60 bg-gradient-to-t from-black/40 to-transparent px-6 md:px-10 py-6 text-sm text-neutral-400",
          "relative z-10 border-t border-gray-200 bg-gradient-to-t from-gray-50 to-transparent px-6 md:px-10 py-6 text-sm text-gray-500",
          theme,
        )}
      >
        Built for hackathon speed — frontend only. Wire API calls where marked.
        ✨ • Shortcuts: ⏎ Analyze, ⎋ Reset, ⌘/Ctrl+K Chat
      </footer>
    </div>
  );
}