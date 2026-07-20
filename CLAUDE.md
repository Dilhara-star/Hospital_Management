# Project Instructions for Claude

## Coding style

- Always write **simple, beginner-friendly Django code**.
- Do NOT use advanced or hard-to-understand patterns (e.g. metaclasses, complex generic class-based views, heavy use of mixins, signals-heavy design, advanced ORM tricks, decorators-on-decorators, overly "clever" one-liners).
- Prefer plain, explicit, easy-to-read code over abstraction, even if it's a bit more verbose.
- Function-based views are fine when they keep things simpler than class-based views.
- Keep logic straightforward so the user can easily follow and maintain it.
- Add a comment on **each line of code**, explaining what it does.
- Comments must be in **simple, short English** (easy words, short sentences).

## Reference guides

Two PDF files in the project root are the coding reference for this project. When writing Django code, follow the patterns shown in them instead of inventing new ones:

- `Django Hospital Management Reference.pdf` — ORM queries, forms.py, views, templates, patterns specific to this hospital system (patients, doctors, appointments, medicine stock).
- `Django_FBV_CRUD_Code_Book (1).pdf` — plain function-based view CRUD (list, detail, create, update, delete) for normal models, OneToOne, ForeignKey (one-to-many) and ManyToMany, both with and without `forms.py`.

### Patterns to use from the guides

- **Function-based views only**, using the standard 5-view CRUD shape: `_list`, `_detail`, `_create`, `_update`, `_delete`.
- **ModelForm in `forms.py`** for create/edit forms — build it from the model with `fields = [...]`, use `widgets` for CSS classes, and `clean_<field>()` / `clean()` for validation.
- The **GET-shows-form / POST-saves** pattern: `form = MyForm(request.POST or None, instance=obj)` then `if request.method == 'POST' and form.is_valid(): form.save()`.
- **One shared template for create and update**: an unbound form (`instance=None`) renders empty inputs, `instance=obj` renders it pre-filled — no need for two templates.
- `get_object_or_404()` instead of `.get()` in views, so a missing row shows a 404 page instead of crashing.
- `select_related()` for ForeignKey/OneToOne and `prefetch_related()` for reverse FK/ManyToMany on any list page that loops and reads a related object, to avoid N+1 queries.
- `Q()` objects for OR-style search boxes (e.g. name/phone/NIC search).
- The `messages` framework (`messages.success`, `messages.error`) after every POST that saves or deletes something.
- `Paginator` on list pages once they can grow long (patients, sales, appointments).
- `F('field') - qty` inside `transaction.atomic()` (with `select_for_update()`) whenever code changes a stock/quantity number — this avoids two requests overwriting each other, and is not "clever," it is the safe way to do it.
- `@login_required` on internal (dashboard) views.
- Register every model in `admin.py` so there is always a free back-office view of the data.

### Patterns from the guides to still avoid

Some sections of the Hospital reference guide (signals, custom context processors, `settings.py`/env-var setup) show more advanced Django features. Do not use these unless the user explicitly asks — they conflict with the beginner-friendly rule above. Prefer writing the same logic directly and explicitly inside a view instead.

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
