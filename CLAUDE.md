# Project Instructions for Claude

## Coding style

- Always write **simple, beginner-friendly Django code**.
- Do NOT use advanced or hard-to-understand patterns (e.g. metaclasses, complex generic class-based views, heavy use of mixins, signals-heavy design, advanced ORM tricks, decorators-on-decorators, overly "clever" one-liners).
- Prefer plain, explicit, easy-to-read code over abstraction, even if it's a bit more verbose.
- Function-based views are fine when they keep things simpler than class-based views.
- Keep logic straightforward so the user can easily follow and maintain it.
- Add a comment on **each line of code**, explaining what it does.
- Comments must be in **simple, short English** (easy words, short sentences).

## Template folder structure

- Inside `templates/`, make one folder per app or feature, so files are grouped and easy to find.
- Example: patient-related frontend pages go in `templates/frontend/patient/`, profile pages go in `templates/frontend/profile/`, appointment pages go in `templates/frontend/appointment/`.
- Shared layout files (base, header, footer, sidebar, topbar) go in a `layouts/` folder for each area (`templates/dashboard/layouts/`, `templates/frontend/layouts/`).
- The app's own root page (e.g. `index.html`) can stay directly inside the app's template folder, not in a subfolder.
- Login/register/password pages go in an `auth/` folder.
- Current structure:
  - `templates/dashboard/` → `layouts/`, `auth/`, `appointment_management/`, `patient_management/`, `staff_management/`, `user_management/`, plus `index.html`
  - `templates/frontend/` → `layouts/`, `appointment/`, `patient/`, `profile/`, plus `index.html`
- When adding a new feature, create a new matching folder instead of dropping the HTML file loose in the parent folder.
