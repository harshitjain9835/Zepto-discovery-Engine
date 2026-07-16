# Problem Statement: AI Discovery Engine — Zepto

## Objective
Build an AI system that continuously mines Zepto’s own review channels (App Store, Play Store, Trustpilot, Reddit, and forums) to explain why Monthly Active Customers stay locked into a narrow, repeat basket. The system should also surface what would make them trust and try new categories such as personal care, baby, pet, pharmacy, and Supermall so Growth can design interventions grounded in real user language rather than assumptions.

## What the system does
The system will:
- Continuously ingest reviews and public discussions from multiple sources
- Use review sources such as:
  - Play Store: https://play.google.com/store/apps/details?id=com.zeptoconsumerapp&hl=en_IN
  - App Store: https://apps.apple.com/in/app/zepto-groceries-in-minutes/id1575323645?see-all=reviews&platform=iphone
  - Reddit: https://www.reddit.com/search/?q=Reviews+of+Zepto+Service+in+india&cId=f4c2ed62-4010-40b0-9738-cc673e019b94&iId=52089c62-0722-4478-9394-f24d1ed62e95
- Deduplicate and translate code-mixed Hindi/English text
- Tag each review for:
  - category mentioned
  - behavior signal such as repeat purchase, category-switch attempt, avoidance, or trust concern
  - sentiment
  - the user’s stated reason
- Cluster tagged reviews into themes and label each theme with a specific research question such as why repeat purchase occurs, what blocks exploration, or what triggers trial
 - Synthesize themes into ranked, evidence-backed insight cards with frequency counts, source mix, and representative examples
 - Re-run monthly so Growth can evaluate whether shipped interventions have actually shifted the conversation, not just the metrics

## Conversational access (Chatbot)
- Provide a conversational QA interface (chatbot) backed by the insight repository and chunked embeddings so stakeholders can ask ad-hoc questions and get evidence-backed answers.
- The chatbot should be able to answer discovery questions such as:
  - Why do users repeatedly buy from the same categories?
  - What prevents users from exploring new categories?
  - How do users discover products today?
  - What role do habits play in shopping behavior?
  - What information do users need before trying a new category?
  - What frustrations emerge repeatedly?
  - Which user segments are more likely to experiment?
  - What unmet needs emerge consistently across discussions?
- Every chatbot response must be traceable to supporting review excerpts or insight cards, with links to source evidence for audit.

## Key requirements
- Multi-source ingestion from Play Store, App Store, Trustpilot, Reddit, and first-party PDP reviews, refreshed on a scheduled cadence
- Structured, queryable output through an Insight Repository rather than a one-off slide deck
- Confidence scoring: a theme should meet a frequency threshold across at least two sources before it is considered actionable
- Human-in-the-loop audit sampling to detect LLM mislabeling before it influences roadmap decisions
- Traceability of every insight back to real source text for auditability and stakeholder trust

## Non-goals
The system is not intended to:
- Function as a real-time customer support or complaint-routing tool
- Make merchandising or catalogue-sourcing decisions on its own
- Replace structured user research such as interviews or usability testing; it serves as a discovery layer that tells Growth where to focus that research
- Directly fix general fulfillment or quality issues, although it will surface them where they block category trust

## Who this helps
- Growth PMs: evidence for prioritizing discovery interventions
- Category and merchandising teams: identifying categories with the highest trust friction to solve first
- Trust & safety and operations teams: visibility into which quality issues most damage cross-category expansion, not just repeat orders
- Leadership and IPO narrative stakeholders: a defensible, evidence-based story for AOV and category-depth expansion

## Top themes from real Zepto review data
- Fulfillment trust gaps bleed into category trust. Recurring complaints about damaged packaging, missing items, and expired products on familiar categories such as produce and dairy make unfamiliar first-time purchases in categories like personal care or baby feel riskier rather than safer.
- Opaque cart controls block exploration before it starts. Unexplained purchase limits and items silently vanishing from the cart discourage users from adding anything outside their normal basket.
- Support responsiveness collapses trust fast. Slow or dismissive support on a quality issue, especially during a first-time order, reads as “don’t try this again” rather than just “this order went wrong.”
- Speed sells commodity trust, not brand trust. Reviews praise delivery speed and live tracking, but that praise clusters around familiar restock items such as drinks and groceries; speed alone does not address unfamiliarity with unfamiliar SKUs or brands.

## Representative user quotes
- “delivered with damaged packaging” — Trustpilot review, on a first-time face wash order
- “You can’t decide what I can get.” — Play Store review, on unexplained cart quantity limits
- “no one connected me for 30 mins” — App Store review, on support response time after an order issue

## Action ideas
- Category starter kits with trial-size SKUs to de-risk first purchase in personal care, baby, pet, and similar categories
- Category-specific micro-reviews on PDPs rather than relying only on overall app ratings
- Transparent cart-limit messaging that explains why a limit applies instead of silently removing items
- Trigger-event targeting based on life-stage signals such as first baby-category or pet-food searches to provide reassurance content rather than only discounts
- Visible quality guarantees at the category level, including explicit replace/refund promises at first-time purchase in a new category

## What this solves
This approach replaces guesswork about why category expansion is stalling with a standing, evidence-based system. It helps Growth ship fixes for real friction around trust instead of defaulting to generic discovery UI such as banners or push notifications that users are already tuning out.
