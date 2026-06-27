# PCFB

## Running the UI

The UI is a Next.js app located in [pcfb-ui/](pcfb-ui/).

### Prerequisites

- Node.js (v18+)
- npm

### Setup

```bash
cd pcfb-ui
npm install
```

### Development

```bash
npm run dev
```

The app will be available at [http://localhost:3000](http://localhost:3000).

### Production

```bash
npm run build
npm run start
```

## Project Structure

```
pcfb-ui/src/
├── app/
│   ├── page.tsx              # Root — redirects to /control
│   ├── layout.tsx            # Root layout (fonts, global styles)
│   ├── globals.css
│   ├── (app)/                # Route group for the main app shell
│   │   ├── layout.tsx        # Shared layout: sidebar + site header
│   │   ├── control/          # Control Center page (/control)
│   │   └── predictions/      # Weekly Predictions page (/predictions)
│   └── dashboard/            # Standalone dashboard page
├── components/
│   ├── app-sidebar.tsx       # Primary navigation sidebar
│   ├── site-header.tsx       # Top header bar
│   ├── nav-main.tsx          # Main nav links
│   ├── nav-documents.tsx     # Documents section in sidebar
│   ├── nav-secondary.tsx     # Secondary nav (settings, help)
│   ├── nav-user.tsx          # User profile in sidebar footer
│   ├── chart-area-interactive.tsx  # Recharts area chart component
│   ├── data-table.tsx        # TanStack Table data table
│   ├── section-cards.tsx     # Summary/stat card grid
│   └── ui/                   # shadcn/ui primitives (button, card, etc.)
├── hooks/
│   └── use-mobile.ts         # Responsive breakpoint hook
└── lib/
    └── utils.ts              # Tailwind class merge utility (cn)
```

### Key technologies

- **Next.js 16** with the App Router
- **shadcn/ui** for UI components (built on Radix UI + Tailwind CSS v4)
- **Recharts** for charts
- **TanStack Table** for data tables
- **dnd-kit** for drag-and-drop
