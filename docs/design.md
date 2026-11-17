# ParkPilot — design.md

Mimic the two reference images. This file overrides any earlier visual direction (including the road-sign / asphalt style in the first canvas).

- **Ref 1 (analytics dashboard):** soft, airy SaaS look. Left sidebar, white rounded cards, big bold numbers, donut and bar charts, one card floating over another for depth.
- **Ref 2 (parking app):** an aerial view of a parking structure with cars, glass-like floating panels on top, icon rail on the left, status tags (Available, Occupied, EV), a trend line with a callout bubble, and a lot occupancy gauge.

Combine them: **Ref 2's aerial parking scene as the hero, Ref 1's card language around it.**

## Look and feel

- Light, calm, premium. Lots of white space. Soft shadows, never hard borders.
- Frosted-glass panels (`backdrop-blur`, 70–85% white) floating over the parking scene.
- Rounded everything: panels 20–24px, buttons and tags fully rounded or 12px.
- One warm accent used sparingly for emphasis and charts.

## Tokens

| Token | Value |
|---|---|
| Page background | `#F6F1EC` (warm off-white, soft peach glow top-left) |
| Surface | `#FFFFFF`, glass: `rgba(255,255,255,.78)` |
| Ink | `#1F2430` |
| Muted text | `#6B7280` |
| Accent | `#E8553D` (coral red, as in Ref 1) |
| Accent soft | `#FDE7E2` |
| Available | `#1FA971` on `#DDF5EA` |
| Occupied | `#E8553D` on `#FDE7E2` |
| Unavailable / EV | `#3B82F6` on `#E0ECFF` |
| Forecast | `#F5A524` dashed line, `#FFF3D6` band |
| Dark button | `#14171F`, white text |
| Asphalt (scene) | `#C9CED6` light concrete, lane markings `#FFFFFF`, bay lines `#FFFFFF` |

- Font: **Poppins** (or Plus Jakarta Sans). Headings 600, big numbers 700, body 400/500.
- Scale: 12 / 14 / 16 / 20 / 28 / 48–64 (hero numbers).
- Shadows: `0 10px 30px rgba(31,36,48,.08)`. Spacing on a 4px grid.
- Status is never color alone: pair color with a text tag or icon.

## Layout

- **Left icon rail** (72px, white, rounded): logo, Live lot, Simulate, Insights, Events, Settings. Active item has an accent pill.
- **Top bar:** page title, small "Simulation running · updated 14:32:08" status with a pulsing dot, search optional.
- **Cards:** CSS grid, 12 columns, 24px gap.

## Screens

### 1. Live lot (hero)
- Large aerial scene filling the main area (see Car simulation below).
- Floating glass panel on the left, like Ref 2's "Suggested spots": tabs `Available 9`, `Occupied 11`, a list of recent events with tags (Arrived / Left), bay, vehicle ID, time.
- Floating callout above a bay when it changes ("P05 · CAR_104 arrived").
- Bottom-right cards: **Lot occupancy** (big `55%`, small gauge or ring, "11 of 20 spaces") and a compact **usage trend** sparkline.

### 2. Simulate
- Same scene, with a control dock at the bottom: Start/Stop simulation (dark button), Send arrival, Send departure, speed slider.
- Right glass panel: last webhook response in a dark code block, then event history with Accepted / Rejected tags.

### 3. Insights
- Ref 1 style grid: big line chart (recorded solid, forecast dashed with band and a callout bubble like Ref 2's "+92.5%"), arrivals/departures bar chart, donut for usage patterns, most-used spaces list, and a **Forecast** card tagged "Forecast · not live" showing "In 30 minutes: ~14 of 20, about 6 free".
- One card may overlap another with a larger shadow, as in Ref 1.

## Real-time car simulation (the signature feature)

The lot must feel alive and show cars physically arriving and leaving as simulated events happen.

**Scene**
- Aerial, slightly tilted view of one lot: 2 rows of 10 bays (P01–P20), a central drive lane, an Entry gate on the left and an Exit gate on the right, light concrete ground, white paint lines, soft shadows under cars, a few planters or curbs for depth.
- Build with SVG (or absolutely positioned divs) inside a container with a gentle CSS perspective (`rotateX` about 20–30deg). Cars are vector sprites seen from above with visible windshield, roof, and shadow. Use 5–6 body colors and 2–3 body shapes (sedan, SUV, hatchback). Pick color and shape deterministically from the `vehicle_id` so a car looks the same every time.

**Behavior (driven by real backend events)**
1. On page load, draw a parked car in every occupied bay with no animation.
2. Poll the API. Diff the previous and current space lists.
3. **Space became occupied:** spawn a car at the Entry gate, drive along the lane with ease-in-out, slow down near the target bay, turn about 90deg, reverse or pull in, settle with a small bounce. Bay outline glows green, then the callout appears. Mark the bay "incoming" until the car arrives, then occupied.
4. **Space became available:** car brakes lights on, backs out of the bay, turns onto the lane, drives to the Exit gate and fades out past it. Bay outline pulses briefly, then shows Available.
5. Queue events so cars never overlap. If events arrive faster than animations, speed animations up slightly (max 2x) instead of dropping them.
6. Motion uses waypoints (entry, lane point in front of the bay, bay center, exit) and Framer Motion for position and rotation. Duration about 2.5–4s per trip.
7. Gate barriers lift when a car passes.
8. The backend is the source of truth. The animation is a visual layer and must never change data. If the animation falls behind or the tab was hidden, snap to the current state.
9. Respect `prefers-reduced-motion`: skip driving, fade cars in and out of bays.

**Bay states in the scene**
- Available: empty bay, thin green outline, small "P07" label.
- Occupied: car inside, subtle red tint on the bay label.
- Unavailable: hatched grey bay.

## Components checklist

Glass panel, status tag, event row, stat card with big number, occupancy ring, line chart with forecast band and callout, bar chart, donut, dark primary button, soft secondary button, icon rail, car sprite, bay, gate.

## Rules

- Keep it clean. Remove any decoration that does not help understanding.
- Forecast visuals (dashed, amber, "Forecast · not live" tag) must always look different from live data.
- Use real data from the API for every number. Use `[placeholder]` where something is not measured yet.
- Responsive: panels stack under the scene on narrow screens. Keep tap targets at least 44px.
- Visible keyboard focus, readable contrast, labeled charts.
