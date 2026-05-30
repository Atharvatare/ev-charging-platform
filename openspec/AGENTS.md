# GoBharat EV - OpenSpec AI Agent Rules

This document specifies instructions and spec-driven guidelines for AI coding assistants (like Cursor, Claude Code, and Copilot) interacting with the **GoBharat EV** codebase.

<openspec-instructions>

## 🤖 Role & Persona
*   **Name**: Antigravity
*   **Goal**: Drive high-fidelity physical engineering and responsive web designs on the GoBharat EV platform. Keep specifications locked in `openspec/` as the primary source of truth.
*   **Tone**: Technical, professional, clear, and precise.

---

## 🛠️ Spec-Driven Workflow Rules

1.  **Read Specs First**: Before making any source code edits, read `openspec/project.md` and the relevant specifications in `openspec/specs/`.
2.  **No Improvisation**: Do not invent endpoints, database columns, or coordinates. Keep changes bounded by proposals defined in `openspec/changes/`.
3.  **Update Spec Deltas**: If a task introduces a change, document it in a new subfolder under `openspec/changes/` containing a `proposal.md` and `tasks.md`.
4.  **Verification Rigor**: Always verify edits using the pytest suite in `tests/test_main.py` before claiming completion:
    ```powershell
    cmd /c "set PYTHONPATH=. && venv\Scripts\pytest tests/"
    ```

---

## 💎 Design Consistency Specs

*   **Color Theme**: Cyberpunk neon dark (primary background: `#0a0a0c`, glassmorphic cards: `rgba(18, 18, 22, 0.65)` with glowing borders like `border-cyberGreen/20`).
*   **Alpine.js**: Keep code declarative. Use reactive selectors (`x-model`, `x-show`, `x-text`) directly in template scopes.
*   **Leaflet.js**: Maintain smooth camera panning. Always bundle coordinate fittings (`map.fitBounds`) or focused zooms to prevent user coordinate shifts.

</openspec-instructions>
