---
name: Network Ops Center Control
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#434655'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#737686'
  outline-variant: '#c3c6d7'
  surface-tint: '#0053db'
  primary: '#004ac6'
  on-primary: '#ffffff'
  primary-container: '#2563eb'
  on-primary-container: '#eeefff'
  inverse-primary: '#b4c5ff'
  secondary: '#565e74'
  on-secondary: '#ffffff'
  secondary-container: '#dae2fd'
  on-secondary-container: '#5c647a'
  tertiary: '#0051b1'
  on-tertiary: '#ffffff'
  tertiary-container: '#0f69dc'
  on-tertiary-container: '#edf0ff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dbe1ff'
  primary-fixed-dim: '#b4c5ff'
  on-primary-fixed: '#00174b'
  on-primary-fixed-variant: '#003ea8'
  secondary-fixed: '#dae2fd'
  secondary-fixed-dim: '#bec6e0'
  on-secondary-fixed: '#131b2e'
  on-secondary-fixed-variant: '#3f465c'
  tertiary-fixed: '#d8e2ff'
  tertiary-fixed-dim: '#adc6ff'
  on-tertiary-fixed: '#001a42'
  on-tertiary-fixed-variant: '#004395'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Inter
    fontSize: 22px
    fontWeight: '700'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 22px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.03em
  code-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
  code-xs:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 14px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1.25rem
  gutter-mobile: 0.75rem
  margin: 1.5rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1.25rem
  space-xl: 2rem
---

## Brand & Style

### Personality & Direction
The design system embodies the balance of precision, operational urgency, and cognitive calm necessary for high-stakes network operations and IT service management. It delivers an enterprise-grade administration interface inspired by high-velocity workflow tools like Linear, while retaining the robust triage capabilities of modern ITSM platforms. The visual language conveys competence, instant clarity, and stability under pressure.

### Design Movement
**Modern Technical Enterprise**: Grounded in structured utility, clean data density, and calm surfaces. The system pairs dark command surfaces (navigation sidebar, global triage bar) with ultra-clean, daylight canvas work areas to sharply separate navigation control from ticket investigation and resolution.

### Emotional Response
- **Trust & Absolute Reliability**: Operators trust that numbers, timestamps, and network statuses reflect live infrastructure states without visual ambiguity.
- **Cognitive Relief**: High-density ticket lists and system logs use quiet, low-contrast scaffolding so critical network alerts, SLA breaches, and error states stand out immediately.
- **Systematic Speed**: Keyboard shortcuts, crisp row highlights, and distinct status color-coding streamline dispatch, assignment, and escalation.

## Colors

### Surface & Canvas Architecture
- **App Canvas (`#F8FAFC`)**: Base page background for all dashboards, ticket feeds, and audit logs.
- **Surface Elevation 0 (`#FFFFFF`)**: Pure white cards, ticket detail drawers, modal bodies, and dropdown menus.
- **Control Bar & Navigation (`#0F172A` & `#1E293B`)**: The deep navy sidebar and global header frame the workspace, grounding the visual hierarchy and establishing professional context.

### Structural & Border Tokens
- **Default Divider / Border (`#E2E8F0`)**: Hairline 1px borders between table rows, KPI metric boundaries, and form sections.
- **Subtle Surface Highlight (`#F1F5F9`)**: Hover state on ticket rows, chip backgrounds, and disabled field fills.
- **Active Selection Border (`#93C5FD`)**: Focused inputs, multi-ticket selection outlines, and drag targets.

### Status & Severity Palette
Status tokens are paired strictly with tinted background pills and sharp foreground text:
- **Urgent / Outage / Escalated (`#EF4444`)**: Critical network failures, SLA breaches, unreachable core switches. Text: `#B91C1C`, Fill: `#FEF2F2`.
- **In Progress / Investigating (`#3B82F6`)**: Actively worked tickets, automated route failover testing. Text: `#1D4ED8`, Fill: `#EFF6FF`.
- **Pending / Warning / Throttled (`#F59E0B`)**: High CPU threshold alerts, awaiting user response, SLA 80% limit warning. Text: `#B45309`, Fill: `#FFFBEB`.
- **Resolved / Normal Operation (`#22C55E`)**: Packet delivery restored, closed incidents, stable nodes. Text: `#15803D`, Fill: `#F0FDF4`.
- **Closed / Archived (`#64748B`)**: Retired incidents, muted channels, read-only audit records. Text: `#475569`, Fill: `#F1F5F9`.

## Typography

### Font Choice & Vietnamese Optimization
`Inter` handles all display titles, structured body copy, table headers, and form inputs. Its tall x-height and clear diacritic rendering accommodate Vietnamese tonal marks (dấu hỏi, ngã, nặng, huyền, sắc) across dense multi-column ticket views without vertical overlap.

`JetBrains Mono` handles IP addresses (IPv4/IPv6), MAC addresses, port IDs, command snippets, ticket ticket-IDs (`#NET-4091`), and SLA countdown timers to ensure tabular numerical alignment.

### Typographic Rules
- All table headers must render in `label-sm`, transformed to uppercase, with neutral text (`#64748B`).
- Incident IDs and machine addresses must use `code-sm` or `code-xs`.
- Form inputs default to `body-md` (14px) to retain high screen density while remaining legible on mobile without triggering iOS auto-zoom.

## Layout & Spacing

### Shell & Layout Blueprint
- **Sidebar Navigation**: Fixed 260px desktop width (`#0F172A`), collapsing to a 64px icon-only rail on compact screens, and a slide-over drawer on mobile viewports (<768px).
- **Workspace Canvas**: Fluid container with a max-width cap of 1680px for wide NOC dashboards.
- **Split Triage Layout**: 
  - Left panel: Ticket list and live queue (380px to 480px width or fluid 40%).
  - Right panel: Ticket detail, network telemetry, topology logs, and conversation thread (fluid 60%).

### Breakpoints & Adaptability
- **Desktop (>= 1280px)**: 12-column grid or dual-pane inspection interface. Sidebar locked at 260px.
- **Tablet / Laptop (768px - 1279px)**: 8-column layout. Sidebar collapses to 64px icon rail. Detail view slides out as a layered drawer over the list.
- **Mobile (< 768px)**: 4-column layout. Full-width views with stack navigation (List View transitions to full-screen Ticket Detail).

## Elevation & Depth

### Atmospheric Stacking
Rather than heavy physical drop shadows, the system uses low-contrast hairline borders combined with soft ambient diffusion:

1. **Level 0 (Floor)**: Canvas background `#F8FAFC`. Zero elevation.
2. **Level 1 (Cards, KPI Modules, List Rows)**: `#FFFFFF` surface with a 1px solid border (`#E2E8F0`) and an ambient micro-shadow: `0 1px 2px 0 rgba(15, 23, 42, 0.04)`.
3. **Level 2 (Popovers, Filter Menus, Hovering Cards)**: `#FFFFFF` surface, 1px border (`#CBD5E1`), shadow: `0 4px 6px -1px rgba(15, 23, 42, 0.07), 0 2px 4px -2px rgba(15, 23, 42, 0.05)`.
4. **Level 3 (Modals, Global Incident Drawers)**: `#FFFFFF` surface, shadow: `0 20px 25px -5px rgba(15, 23, 42, 0.1), 0 8px 10px -6px rgba(15, 23, 42, 0.06)`. Backed by an overlay scrim of `#0F172A` at 40% opacity with a 2px backdrop blur.

## Shapes

### Edge Philosophy
The system uses tight, modern geometry. Crisp rectangles retain structural discipline for high-density tables and data trees, softened with intentional radius tiers:
- **Base Elements (Buttons, Inputs, Row Selectors, Badges)**: 6px to 8px border radius (`rounded-md` to `rounded-lg`).
- **Containers (Cards, Modal Windows, KPI Widgets)**: 12px border radius (`rounded-xl`).
- **Status Indicators & Avatars**: True pill (`rounded-full`) reserved strictly for count pills, ping status dots, and team member profile avatars.

## Components

### Buttons
- **Primary**: Solid `#2563EB` fill, white bold text, height 36px (compact) or 40px (standard), border-radius 8px. Hover: `#1D4ED8`. Active: `#1E40AF`. Focus: 2px offset ring in `#93C5FD`.
- **Secondary / Outline**: `#FFFFFF` background, 1px border `#E2E8F0`, text `#1E293B`. Hover: `#F8FAFC`, border `#CBD5E1`.
- **Destructive**: Solid `#EF4444` for irreversible actions (e.g., "Hủy hạ tầng / Purge Cache"). Sub-actions use text `#EF4444` on `#FEF2F2`.
- **Ghost / Icon Action**: Transparent fill, neutral icon `#64748B`. Hover: `#F1F5F9`, text `#0F172A`.

### Status Badges & Priority Chips
- Badges use 11px uppercase `JetBrains Mono` or 12px `Inter` medium with 4px vertical padding and 8px horizontal padding.
- **Open**: Fill `#EFF6FF`, Border `#BFDBFE`, Text `#1D4ED8`.
- **In Progress**: Fill `#EFF6FF`, Border `#60A5FA`, Text `#2563EB`, accompanied by a blinking 6px status dot.
- **Resolved**: Fill `#F0FDF4`, Border `#BBF7D0`, Text `#15803D`.
- **Closed**: Fill `#F1F5F9`, Border `#E2E8F0`, Text `#475569`.
- **Urgent / P1**: Fill `#FEF2F2`, Border `#FECACA`, Text `#DC2626`, accompanied by an alert icon.

### Form Inputs & Select Controls
- Standard input height: 38px. Font: `Inter` 14px.
- Idle: 1px border `#E2E8F0`, background `#FFFFFF`, text `#0F172A`, placeholder `#94A3B8`.
- Focus: Border `#2563EB`, ring 3px `rgba(37, 99, 235, 0.15)`.
- Error state: Border `#EF4444`, ring 3px `rgba(239, 68, 68, 0.15)`. Support message displayed below in 12px `#EF4444`.

### Cards & KPI Metric Blocks
- Metric widgets feature a 1px `#E2E8F0` border on `#FFFFFF` with 16px to 20px internal padding.
- Structure: Metric title (13px, `#64748B`), current value (28px `Inter` bold, `#0F172A`), comparative trend badge (e.g., `+12.4% so với hôm qua` in green or red pill badge) and sparkline container.

### Ticket Incident Table
- Row height: 48px standard, 38px dense view.
- Row striping: White base, alternating with transparent hover highlight `#F8FAFC`.
- Selected row: `#EFF6FF` background with a 2px left border in `#2563EB`.
- Columns: Ticket Key (`code-sm`), Subject with priority icon (`body-md` semi-bold), Requester/Department (`body-sm`), Assigned Agent (`avatar` + `name`), Status Badge, SLA Timer (color-coded count-down).

### Timeline & Audit Trail
- Left-anchored 2px vertical spine in `#E2E8F0`.
- Event nodes use 24px circular iconography representing lifecycle events (Created, Assigned, Node Rebooted, Resolved).
- Internal technical notes display with a soft amber-tinted container (`#FFFBEB`, border `#FDE68A`) to distinguish internal chatter from customer-visible replies.