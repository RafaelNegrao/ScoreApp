# Score App – Presentation Script

---

## Introduction

Good morning/afternoon. I am going to walk through the Score App, the desktop solution we built to keep supplier performance data in one place. The goal is simple: make it effortless to monitor every supplier, spot trends early, and act with confidence because every number is auditable and sourced directly from our internal database.

---

## Login Screen

**Credential Form** – Users enter their WWID and password. We support credential caching for trusted devices, so daily users do not have to retype their information, yet every login is still logged.

**Self-Registration Link** – New team members can request access on their own. The workflow records the request, so admins only need to approve it.

**Session Indicator** – A subtle footer shows whether the app is online and ready to sync. If the database is offline, the user sees it before trying to work.

---

## Home Page (Dashboard)

**Headline Cards** – Four tiles summarize the health of the environment: total suppliers in the system, total assessments recorded, current average score, and number of active users. The cards update instantly when new data arrives, so leadership always sees the same snapshot.

**Insights Carousel**
- *Profile Panel* – Displays the logged-in person’s name, WWID, and privilege tier, which helps confirm they are in the right account.
- *Permissions Panel* – Lists which criteria (OTIF, NIL, Pickup, Package) that user can edit. This avoids accidental edits by people who only have view rights.
- *System Panel* – Shows the app version, database status, and last sync time, so IT can diagnose issues quickly.
- *Active Users Panel* – Exclusive to Super Admins, this highlights the five most active users to recognize heavy contributors or spot unusual access patterns.

---

## Score Page (Core Workspace)

**Search Workspace** – On the Research tab, the analyst picks suppliers by typing a name, supplier ID, or PO. They select the month and year, can multi-select suppliers, and the grid loads every historical note for context before new data is entered.

**Editable Score Grid** – Each supplier row contains four score inputs: OTIF, NIL, Pickup, and Package. The app enforces numeric ranges, and as soon as a score changes, the total score recalculates using the configured weights.

**Comment Column** – Every month allows a text note for context. These notes appear later in Timeline and Logs, so a future reviewer understands why a score was adjusted.

**Autosave Toggle** – Writers can choose between manual save (for batch edits) or autosave (ideal when scoring supplier-by-supplier). Either way, the save indicator confirms when everything is secured.

**Criteria Guide Tab** – This tab teaches the scoring logic visually. OTIF converts percentages directly (87% becomes 8.7). NIL, Pickup, and Package follow the incident ladder: zero incidents yields 10, one incident drops to 5, anything above one falls to 0. It keeps reviewers aligned when interpreting raw logistics data.

**Action Menu** – The three-dot menu in the header unlocks power features: export the assessment template to Excel, import bulk results from spreadsheets, and issue a “full score” action when a month needs blanket 10s (for example, when a supplier had no activity but must stay compliant).

---

## Risks Page (Early Warning Board)

**Year Filter** – Leadership can look back historically or focus on the current year without changing any other page-level settings.

**Supplier Cards** – Each card pulls together the supplier name, BU, PO, SSID, and internal ID. The annual average score appears upfront to tell the story in a single glance.

**Monthly Bar Strip** – A tight bar chart shows month-by-month performance so that outlier months stand out immediately.

**Quarter Blocks** – Q1 through Q4 averages are listed with up or down arrows, clarifying whether a quarter is trending positively or negatively compared to the prior one.

**Color Coding** – Green cards exceed the target, yellow hover near the threshold, and red fall short. Managers can scan the page and focus on the red band first during monthly reviews.

---

## Timeline Page (Deep Dive)

**Supplier Selector** – Once a supplier is chosen, every metric on the page pivots to their data set, encouraging one-on-one performance reviews.

**Metrics Deck** – The top row shows the lifetime average, the trailing 12-month average, and the selected year’s average. Another strip covers Q1–Q4 with micro trend icons, which makes quarter closes more factual.

**Charting Suite** – The Charts tab renders the overall score trend with the target line for context. Beneath it, four mini charts isolate OTIF, NIL, Pickup, and Package so the reviewer can see which discipline is dragging the total down.

**Hover Details** – Hovering a point reveals the exact month, score, and comment snippet, allowing managers to ask precise follow-up questions.

---

## Lists Page (Supplier Registry)

**Data Grid** – Columns include ID, SSID, Supplier Name, PO, BU, status, and assigned SQE/PU contacts. The list supports multi-column sorting and filters, making it easy to home in on a BU or buyer portfolio.

**Inline Editing** – Authorized users can correct fields directly in the grid. Every change is logged, so data stewardship remains controlled.

**Bulk Operations** – Importing from Excel keeps the registry aligned with ERP exports, and exporting out offers instant reporting for external stakeholders.

**Status Badge** – Active suppliers show a green chip, inactive ones display gray, so the team never confuses retired suppliers with current partners.

---

## Users Page (Access Control)

**User Directory** – Displays each user’s name, WWID, email, and role. Admins can create or edit profiles without leaving the page.

**Privilege Ladder** – Roles are explicit: Super Admin has full control, Admin covers operational management, and User is optimized for data entry. Changing roles updates permissions instantly.

**Permission Matrix** – Beyond roles, each person can have granular rights per criterion (OTIF, NIL, Pickup, Package). This ensures, for example, that logistics specialists only touch NIL and Pickup while quality engineers handle Package.

**Lifecycle Controls** – Toggle switches activate or deactivate accounts, which is useful when someone is on leave or no longer in the program.

---

## Settings Page (Control Center)

**General Tab** – Houses the autosave switch, theme selector (light/dark), and the global refresh toggle. It is where people personalize the UI.

**Target Tab** – Defines the passing average for the year (for instance 8.7). The value feeds the Risks page and any color-coding logic elsewhere.

**Weights Tab** – Lets leadership rebalance the relative importance of OTIF, NIL, Pickup, and Package. The interface enforces a 100% total, so the math is always valid.

**Privileges Tab** – Maps which role can reach each major feature. It is the policy layer that ensures the right controls stay behind the right clearance level.

**Logs Tab** – Surfaces every action with timestamp, user, and payload before/after. Auditors can sort by action type or date range when investigating a change.

**Info Tab** – Provides the official app summary: version, maintainers, tech stack, and the feature list. It doubles as the quick brief for onboarding new stakeholders.

---

## Benefits Snapshot

1. **Single Source** – All supplier assessments live in one repository, ending the spreadsheet chase.
2. **Audit Trail** – Every edit carries a username and timestamp, simplifying compliance work.
3. **Visual Clarity** – Dashboards, cards, and charts make it easy to explain trends to leadership.
4. **Proactive Risking** – The Risks page highlights problems before they become supplier crises.
5. **Configurable Rules** – Targets and weights adjust without code changes, so the process can evolve.
6. **Role-Based Security** – Privileges and per-criterion rights keep sensitive data under control.
7. **Operational Efficiency** – Bulk imports/exports and autosave reduce manual overhead.

---

## Closing

The Score App replaces a fragmented evaluation process with a single, traceable workflow. It is built with React and TypeScript on the front end, Rust via Tauri on the back end, and SQLite as the embedded database, which gives us desktop performance with enterprise-grade reliability.

Thank you for the time. I am happy to demonstrate any page live or dive deeper into the roadmap.

---

**Developed by:** Rafael Negrão de Souza (AN62H)  
**Intellectual Author:** Cleiton Bianchi dos Santos (IV838)  
**Version:** 1.1.5 | **Date:** Nov/2025
