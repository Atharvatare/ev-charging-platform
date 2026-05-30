# UI/UX Design Brief - GoBharat EV

This brief defines the design system, color palette, typography guidelines, glassmorphism parameters, and layout structures to preserve GoBharat EV’s premium cyberpunk aesthetics.

---

## 🎨 1. Harmonious Cyberpunk Color Palette

GoBharat EV uses an immersive **neon dark** color palette configured as customizable tailwind tokens and HSL variables:

| Color Token | Variable Name | Hex Code | HSL Representation | Design Intent |
| :--- | :--- | :--- | :--- | :--- |
| **Deep Space** | `--b1` | `#0a0a0c` | `240° 10% 4%` | Base background of all pages. |
| **Cyber Green** | `cyberGreen` | `#22c55e` | `142° 70% 45%` | Available ports, successful route highlights. |
| **Cyber Cyan** | `cyberBlue` | `#06b6d4` | `188° 91° 43%` | Active telemetry graphs, hotline icons. |
| **Cyber Orange**| `cyberOrange`| `#f97316` | `25° 95% 53%` | Occupied chargers, environmental stress buttons. |
| **Cyber Pink** | `cyberPink` | `#ec4899` | `330° 81% 60%` | Maintenance ports, diagnostic fault buttons. |
| **Panel Border**| `--card-border` | `rgba(255,255,255,0.08)` | — | Micro-borders wrapping glassmorphic panels. |

---

## 💎 2. Glassmorphism Design Tokens

All containers and panels must adhere to standard glassmorphic styling to maintain high-fidelity depth:

*   **Background Blur**: Apply `backdrop-filter: blur(16px)` to overlay elements.
*   **Translucency**: Base fill should be semi-transparent: `background-color: rgba(18, 18, 22, 0.65)`.
*   **Micro-Borders**: Wrap cards with extremely thin semi-transparent lines: `border: 1px solid rgba(255, 255, 255, 0.08)`.
*   **Glowing Shading**: Inject subtle colored drop shadows to mimic operational glowing grids:
    *   *Available Glow*: `box-shadow: 0 0 15px rgba(34, 197, 94, 0.12)`.
    *   *Fault Glow*: `box-shadow: 0 0 15px rgba(236, 72, 153, 0.12)`.

---

## ✍️ 3. Typography Hierarchy

*   **Primary Font**: Google Fonts: **Outfit** (`sans-serif`).
    *   *Weights*: Light (`300`), Regular (`400`), Medium (`500`), SemiBold (`600`), Bold (`700`), ExtraBold (`800`).
*   **Monospace Font**: `SFMono-Regular`, `Consolas`, `Liberation Mono`, `monospace` (specifically for database IDs, charging power numbers, and coordinate readings).

### Scale & Styles
*   **Hero Headers**: `text-4xl md:text-6xl font-extrabold tracking-tight text-white mb-4`.
*   **Card Headings**: `text-base font-extrabold text-white`.
*   **Telemetry Readings**: `font-mono text-xs font-bold text-cyberGreen`.
*   **HUD Label Text**: `text-[9px] font-bold text-neutral-400 uppercase tracking-widest`.

---

## 🎬 4. Micro-Animations & Viewport Transitions

All interactive components must use transition animations to feel alive and responsive:

1.  **Drawer Slide-Up Drawer**:
    *   `transition-all duration-350 ease-out transform`.
    *   Triggers slide transitions when topographic routes solve, sliding up from the screen bottom smoothly.
2.  **Telemetry Pulse Indicator**:
    *   Wrap active status indicators in tailwind `animate-ping` alongside static circles, illustrating live database polling continuously.
3.  **Neon Toggle Hover Scale**:
    *   Apply `hover:scale-105 active:scale-95 transition-all duration-300` to action controls.
