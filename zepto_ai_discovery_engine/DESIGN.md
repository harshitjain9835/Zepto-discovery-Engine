---
name: Velocity Discovery
colors:
  surface: '#fbf8ff'
  surface-dim: '#dcd9e0'
  surface-bright: '#fbf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f2fa'
  surface-container: '#f0ecf4'
  surface-container-high: '#eae7ee'
  surface-container-highest: '#e4e1e9'
  on-surface: '#1b1b20'
  on-surface-variant: '#4c4354'
  inverse-surface: '#303035'
  inverse-on-surface: '#f3eff7'
  outline: '#7d7386'
  outline-variant: '#cec2d7'
  surface-tint: '#8027dc'
  primary: '#510096'
  on-primary: '#ffffff'
  primary-container: '#7000cc'
  on-primary-container: '#d6b2ff'
  inverse-primary: '#dab9ff'
  secondary: '#705d00'
  on-secondary: '#ffffff'
  secondary-container: '#fcd400'
  on-secondary-container: '#6e5c00'
  tertiary: '#6e0056'
  on-tertiary: '#ffffff'
  tertiary-container: '#960077'
  on-tertiary-container: '#ffa5dc'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#eedbff'
  primary-fixed-dim: '#dab9ff'
  on-primary-fixed: '#2a0053'
  on-primary-fixed-variant: '#6500b9'
  secondary-fixed: '#ffe16d'
  secondary-fixed-dim: '#e9c400'
  on-secondary-fixed: '#221b00'
  on-secondary-fixed-variant: '#544600'
  tertiary-fixed: '#ffd8ec'
  tertiary-fixed-dim: '#ffaede'
  on-tertiary-fixed: '#3b002d'
  on-tertiary-fixed-variant: '#87006b'
  background: '#fbf8ff'
  on-background: '#1b1b20'
  surface-variant: '#e4e1e9'
typography:
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 40px
    fontWeight: '800'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '800'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '800'
    lineHeight: 32px
  title-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '700'
    lineHeight: 28px
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 16px
  margin-mobile: 16px
  margin-desktop: 32px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 24px
---

## Brand & Style

The brand personality is high-energy, dependable, and intelligently playful. It aims to evoke a sense of "speed with insight," moving beyond simple delivery to become a smart companion for the user's kitchen and lifestyle. The aesthetic is a fusion of **Corporate Modern** efficiency and **Vibrant Boldness**, utilizing saturated colors to signify freshness and momentum. 

To support the discovery engine and AI-driven insights, the system incorporates subtle data-visualization patterns (like halftone dots and progress micro-interactions) while maintaining a clean, professional finish. The goal is to make complex data feel accessible, appetizing, and actionable.

## Colors

This design system is built around a high-contrast palette that prioritizes legibility and brand recognition.

- **Primary (Vibrant Purple):** The anchor of the brand, used for major surfaces, primary buttons, and the brand's core identity.
- **Secondary (Bold Yellow):** Reserved for high-value call-to-actions, limited-time offers, and critical "efficiency" highlights. It provides a sharp contrast to the purple.
- **Tertiary (Electric Pink):** Used for playful accents, notifications, and AI-driven "spark" moments within the discovery engine.
- **Neutral:** A deep "Off-Black" for typography and a series of cool greys for layout structure and secondary text.

For the discovery engine, use tinted variations of the primary purple (10-20% opacity) as background washes to group AI-generated insights without cluttering the UI.

## Typography

The system utilizes **Plus Jakarta Sans** for its approachable yet geometric construction. It strikes the perfect balance between a friendly "grocery" feel and a precise "tech-first" efficiency.

- **Headlines:** Use ExtraBold (800) for high-impact branding. For the discovery engine, use `headline-xl` sparingly for major data milestones.
- **Body:** Standard weight (400) provides excellent readability for product descriptions.
- **Labels:** SemiBold or Bold weights are used for metadata, pricing, and AI-insight tags.
- **Scaling:** For mobile, headlines should scale down to prevent text-wrapping issues in tight grid layouts, while maintaining their heavy weight to preserve brand character.

## Layout & Spacing

The layout follows a **Fluid Grid** model to accommodate the density required for a grocery marketplace while scaling into data-rich discovery dashboards.

- **Mobile:** 4-column layout with 16px margins. Content is mostly stacked or displayed in horizontal carousels.
- **Desktop:** 12-column layout. Discovery insights and data visualizations take up a 4-column sidebar or an 8-column central stage.
- **Rhythm:** An 8pt grid system (with 4px increments for tight components) ensures vertical rhythm. Use `stack-lg` to separate distinct logical sections and `stack-sm` for related items within a card or list.
- **Discovery View:** When viewing AI insights, increase padding to 24px within containers to allow the data visualizations "room to breathe."

## Elevation & Depth

Hierarchy is established through **Tonal Layers** and **Low-Contrast Outlines**.

1.  **Base Layer:** White or very light grey (#F8F8FA) for the main canvas.
2.  **Surface Layer:** White cards with very subtle, extra-diffused shadows (0px 4px 20px rgba(112, 0, 204, 0.06)).
3.  **Insight Layer:** Semi-transparent purple or pink washes to denote AI-generated content.
4.  **Floating Elements:** Primary buttons and critical alerts use a stronger elevation to appear "tappable" and urgent.

Avoid heavy skeuomorphism. Instead, use soft inner-glows on primary purple elements to give them a modern, vibrant "backlit" feel.

## Shapes

The shape language is consistently **Rounded**, signifying friendliness and safety.

- **Cards & Inputs:** 0.5rem (8px) corner radius.
- **Secondary Buttons & Chips:** 1rem (16px) or full pill-shaped to differentiate them from primary action containers.
- **Discovery Dashboard Elements:** Use slightly larger 1rem radii for insight "bubbles" to make them feel distinct from standard product cards.
- **Imagery:** Product photography should always have a matching 8px or 16px corner radius to feel integrated into the UI.

## Components

### Buttons
- **Primary:** Purple background, white text, Bold weight. High-density padding.
- **Accent:** Yellow background, Neutral-Black text. Used specifically for "Add to Cart" or "Buy Now."
- **Ghost:** Purple outline, transparent background. Used for secondary navigation.

### Discovery Chips
Used for filtering and AI categories. Use a light purple background (#F3E8FF) with deep purple text. When active, transition to solid purple with white text.

### Data Visualization (Discovery Engine)
- **Bar Charts:** Use rounded caps on all bars. Primary color for current data, Grey for benchmarks.
- **Insight Cards:** Feature a small "Spark" icon (Tertiary Pink) and a soft tinted background.
- **Halftone Patterns:** Use subtle dot-matrix patterns as background decorations for AI-driven sections to evoke a "processed data" aesthetic.

### Input Fields
Clean white backgrounds with a 1px border (#E2E2E8). On focus, the border transitions to Primary Purple with a 2px stroke.

### Cards
- **Product Card:** Image-heavy, 8px rounded corners, price in Bold, Secondary color used for the "+" add button.
- **Insight Card:** Text-heavy, 16px rounded corners, utilizing `title-md` for the primary takeaway.