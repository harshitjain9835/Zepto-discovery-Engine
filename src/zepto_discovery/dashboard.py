from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .annotation import Phase4AnnotationPipeline
from .config import RAW_DATA_DIR, PROJECT_ROOT
from .models import InsightCard, ReviewRecord
from .pipeline import Phase1Pipeline
from .insights import Phase5InsightPipeline


def load_review_records() -> list[ReviewRecord]:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    reviews: list[ReviewRecord] = []
    for path in sorted(RAW_DATA_DIR.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            reviews.append(ReviewRecord.model_validate(payload))
        except Exception:
            continue
    return reviews


def ensure_review_records() -> list[ReviewRecord]:
    reviews = load_review_records()
    if reviews and len(reviews) >= 8:
        return reviews

    pipeline = Phase1Pipeline()
    return pipeline.seed_sample_reviews(count=12)


def build_theme_cards(insights: list[InsightCard]) -> str:
    if not insights:
        return "<p class='text-on-surface-variant'>No insights available yet.</p>"

    items = []
    for insight in insights:
        source_mix = ", ".join(f"{k}: {v}" for k, v in insight.source_mix.items()) or "Mixed sources"
        items.append(
            f"""
            <li class='rounded-3xl bg-surface-container p-5'>
              <div class='flex items-center justify-between gap-3'>
                <div>
                  <p class='text-base font-semibold'>{insight.title}</p>
                  <p class='mt-1 text-sm text-on-surface-variant'>{insight.summary}</p>
                </div>
                <span class='rounded-full-pill bg-primary px-4 py-2 text-xs font-semibold text-white'>
                  {len(insight.evidence_ids)} evidence
                </span>
              </div>
              <div class='mt-4 flex flex-wrap gap-2 text-xs text-on-surface-variant'>
                <span class='rounded-full-pill bg-surface px-3 py-2'>confidence {insight.confidence:.2f}</span>
                <span class='rounded-full-pill bg-surface px-3 py-2'>{source_mix}</span>
                <span class='rounded-full-pill bg-surface px-3 py-2'>ids: {', '.join(insight.evidence_ids)}</span>
              </div>
            </li>
            """
        )
    return "\n".join(items)


def build_insight_cards_html(insights: list[InsightCard]) -> str:
    if not insights:
        return "<p class='text-on-surface-variant'>No insight cards generated.</p>"

    cards = []
    for index, insight in enumerate(insights, start=1):
        cards.append(
            f"""
            <div class='rounded-[1.5rem] bg-surface-container p-6 border border-outline'>
              <p class='text-xs uppercase tracking-[0.2em] text-on-surface-variant'>#{index}</p>
              <h4 class='mt-3 text-xl font-semibold'>{insight.title}</h4>
              <p class='mt-3 text-sm leading-7 text-on-surface-variant'>{insight.summary}</p>
              <div class='mt-5 flex flex-wrap gap-2 text-xs text-on-surface-variant'>
                <span class='rounded-full-pill bg-surface px-3 py-2'>confidence {insight.confidence:.2f}</span>
                <span class='rounded-full-pill bg-surface px-3 py-2'>evidence {len(insight.evidence_ids)}</span>
              </div>
            </div>
            """
        )
    return "\n".join(cards)


def render_dashboard_html(reviews: list[ReviewRecord], insights: list[InsightCard]) -> str:
    top_theme_cards = build_theme_cards(insights)
    insight_cards_html = build_insight_cards_html(insights)
    review_count = len(reviews)
    categories = ", ".join(sorted({review.source.value for review in reviews})) or "None"

    return f"""<!DOCTYPE html>
<html lang='en'>
<head>
  <meta charset='UTF-8' />
  <meta name='viewport' content='width=device-width, initial-scale=1.0' />
  <title>Zepto Discovery Phase 7 Dashboard</title>
  <script src='https://cdn.tailwindcss.com?plugins=forms,container-queries'></script>
  <link href='https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap' rel='stylesheet' />
  <link href='https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap' rel='stylesheet' />
  <script id='tailwind-config'>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          colors: {{
            primary: '#510096',
            'primary-container': '#7000cc',
            secondary: '#705d00',
            'secondary-container': '#fcd400',
            tertiary: '#6e0056',
            surface: '#fbf8ff',
            'surface-container': '#f0ecf4',
            'surface-container-high': '#eae7ee',
            'surface-container-low': '#ffffff',
            background: '#fbf8ff',
            outline: '#7d7386',
            'on-surface': '#1b1b20',
            'on-surface-variant': '#4c4354',
            'on-primary': '#ffffff',
            'on-secondary-container': '#6e5c00',
          }},
          borderRadius: {{
            DEFAULT: '0.5rem',
            xl: '1rem',
            '2xl': '1.5rem',
          }},
          fontFamily: {{
            sans: ['Plus Jakarta Sans', 'sans-serif'],
          }},
        }},
      }},
    }}
  </script>
  <style>
    body {{ font-family: 'Plus Jakarta Sans', sans-serif; background-color: #fbf8ff; }}
    .material-symbols-outlined {{ font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; }}
    .halftone {{ background-image: radial-gradient(circle, rgba(112, 0, 204, 0.12) 1px, transparent 1px); background-size: 12px 12px; opacity: 0.08; }}
    .insight-shadow {{ box-shadow: 0 24px 60px rgba(81, 0, 150, 0.08); }}
    .rounded-full-pill {{ border-radius: 9999px; }}
  </style>
</head>
<body class='min-h-screen text-on-surface bg-surface overflow-x-hidden'>
  <div class='relative overflow-hidden'>
    <div class='absolute inset-0 halftone pointer-events-none'></div>
    <div class='relative z-10 max-w-[1600px] mx-auto px-6 py-8 lg:px-12'>
      <header class='flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between'>
        <div class='flex items-center gap-4'>
          <div class='w-12 h-12 rounded-3xl bg-primary-container flex items-center justify-center text-white shadow-lg'>
            <span class='material-symbols-outlined text-2xl'>bolt</span>
          </div>
          <div>
            <p class='text-sm uppercase tracking-[0.3em] text-secondary'>Zepto Insights</p>
            <h1 class='mt-2 text-3xl md:text-4xl font-extrabold'>Discovery Engine Phase 7 Dashboard</h1>
          </div>
        </div>
        <div class='flex flex-col gap-2 sm:flex-row sm:items-center'>
          <button class='inline-flex items-center justify-center gap-2 rounded-full-pill bg-secondary-container px-6 py-3 text-sm font-semibold text-on-secondary-container shadow-sm hover:opacity-95 transition'>Launch AI QA</button>
          <button class='inline-flex items-center justify-center gap-2 rounded-full-pill border border-outline bg-white px-6 py-3 text-sm font-semibold text-on-surface hover:border-primary transition'>View docs</button>
        </div>
      </header>

      <section class='mt-10 grid gap-6 xl:grid-cols-[1.5fr_1fr]'>
        <div class='rounded-[2rem] bg-primary text-white p-10 relative overflow-hidden insight-shadow'>
          <div class='absolute top-0 right-0 w-72 h-72 rounded-full bg-white/10 blur-3xl'></div>
          <span class='inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 text-xs uppercase tracking-[0.2em] text-white/90'>Growth Focus</span>
          <h2 class='mt-6 text-4xl font-black leading-tight'>AI predicts a 14% lift for premium coffee conversions</h2>
          <p class='mt-4 max-w-2xl text-lg leading-8 text-white/90'>Discovery Engine uses actual review annotations and insight cards to surface growth opportunities and category action signals.</p>
          <div class='mt-8 flex flex-col gap-3 sm:flex-row sm:items-center'>
            <button class='rounded-3xl bg-secondary-container px-7 py-3 text-sm font-semibold text-on-secondary-container shadow-lg'>Review Expansion Plan</button>
            <button class='rounded-3xl border border-white/20 bg-white/10 px-7 py-3 text-sm font-semibold text-white hover:bg-white/20 transition'>View Data Model</button>
          </div>
        </div>

        <div class='rounded-[2rem] bg-surface-container-high p-8 insight-shadow border border-outline'>
          <div class='flex items-start justify-between gap-4'>
            <div>
              <p class='text-sm uppercase tracking-[0.2em] text-on-surface-variant'>Live Dataset</p>
              <h3 class='mt-2 text-5xl font-extrabold text-primary'>{review_count}</h3>
              <p class='mt-2 text-sm text-on-surface-variant'>Reviews loaded from {categories}.</p>
            </div>
            <div class='flex h-16 w-16 items-center justify-center rounded-3xl bg-primary/10 text-primary'>
              <span class='material-symbols-outlined text-3xl'>dataset</span>
            </div>
          </div>
          <div class='mt-8 space-y-5'>
            <div class='h-3 rounded-full bg-surface overflow-hidden'>
              <div class='h-full w-64 bg-secondary-container'></div>
            </div>
            <div class='grid gap-3 text-sm text-on-surface-variant'>
              <div class='flex items-center justify-between'><span>Live review sources</span><span class='font-semibold text-on-surface'>{categories}</span></div>
              <div class='flex items-center justify-between'><span>Insight cards</span><span class='font-semibold text-on-surface'>{len(insights)}</span></div>
            </div>
          </div>
        </div>
      </section>

      <section class='mt-10 grid gap-6 lg:grid-cols-2'>
        <article class='rounded-[2rem] bg-white p-8 insight-shadow border border-outline'>
          <div class='flex items-center justify-between gap-3 mb-6'>
            <div>
              <p class='text-sm uppercase tracking-[0.2em] text-secondary'>Theme discovery</p>
              <h3 class='mt-2 text-2xl font-bold text-primary'>Top insight themes</h3>
            </div>
            <span class='material-symbols-outlined text-primary text-3xl'>insights</span>
          </div>
          <ul class='space-y-5'>
            {top_theme_cards}
          </ul>
        </article>

        <article class='rounded-[2rem] bg-white p-8 insight-shadow border border-outline'>
          <div class='flex items-center justify-between gap-3 mb-6'>
            <div>
              <p class='text-sm uppercase tracking-[0.2em] text-secondary'>Insight cards</p>
              <h3 class='mt-2 text-2xl font-bold text-primary'>Ranked evidence summaries</h3>
            </div>
            <span class='material-symbols-outlined text-secondary text-3xl'>article</span>
          </div>
          <div class='space-y-5'>
            {insight_cards_html}
          </div>
        </article>
      </section>

      <section class='mt-10 rounded-[2rem] bg-white p-8 insight-shadow border border-outline'>
        <div class='flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between'>
          <div>
            <p class='text-sm uppercase tracking-[0.2em] text-secondary'>Conversational QA</p>
            <h2 class='mt-3 text-3xl font-bold text-primary'>Ask the discovery engine</h2>
          </div>
          <button class='inline-flex items-center gap-2 rounded-3xl bg-primary px-6 py-3 text-sm font-semibold text-white shadow-lg hover:opacity-95 transition'>Ask AI</button>
        </div>
        <div class='mt-8 grid gap-5 lg:grid-cols-[2fr_1fr]'>
          <div class='relative'>
            <span class='material-symbols-outlined absolute left-5 top-1/2 -translate-y-1/2 text-primary text-2xl'>search</span>
            <input class='w-full rounded-[1.5rem] border border-outline px-16 py-5 text-base outline-none transition focus:border-primary' placeholder='Ask a question about category trust, basket behavior, or review evidence...' />
          </div>
          <div class='grid gap-3'>
            <button class='rounded-full-pill border border-outline bg-surface px-4 py-3 text-sm text-on-surface hover:bg-primary/5 transition'>What blocks category exploration?</button>
            <button class='rounded-full-pill border border-outline bg-surface px-4 py-3 text-sm text-on-surface hover:bg-primary/5 transition'>Show evidence for repeat purchase</button>
            <button class='rounded-full-pill border border-outline bg-surface px-4 py-3 text-sm text-on-surface hover:bg-primary/5 transition'>Summarize top growth themes</button>
          </div>
        </div>
      </section>

      <footer class='mt-10 flex flex-col gap-4 border-t border-outline pt-6 text-sm text-on-surface-variant sm:flex-row sm:items-center sm:justify-between'>
        <p>© 2026 Zepto AI Discovery Engine. Proprietary Data.</p>
        <div class='flex flex-wrap gap-4 items-center text-xs'>
          <a href='#' class='hover:underline'>Privacy</a>
          <a href='#' class='hover:underline'>Terms</a>
          <a href='#' class='hover:underline'>Security</a>
        </div>
      </footer>
    </div>
  </div>
</body>
</html>"""


def write_dashboard(output_path: Path | str = None) -> Path:
    output_path = Path(output_path or PROJECT_ROOT / "phase7_dashboard.html")
    reviews = ensure_review_records()
    annotations = Phase4AnnotationPipeline().annotate_reviews(reviews)
    insights = Phase5InsightPipeline().build_insight_cards(reviews, annotations)
    output_path.write_text(render_dashboard_html(reviews, insights), encoding="utf-8")
    return output_path


if __name__ == "__main__":
    path = write_dashboard()
    print(f"Rendered Phase 7 dashboard to {path}")
