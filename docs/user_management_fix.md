# User Management: Staff/Patient Fix

This is the reference doc for a bug fix and cleanup in the user management
app (`apps/user_management/`), alongside the two PDF guides in the project
root. Follow this shape when touching this app again.

## The bug that was reported

"Adding a staff member saves them in the patient table." Checking the live
database confirmed it: one account (username `pharmacist`, a real staff
member with `role='pharmacist'`) still had a full `PatientProfile` row
(`MRN-00001`) sitting in the database.

The "Add Staff Member" page (`staff_add`) was checked line by line, and in
every past commit — it never created a `PatientProfile`. The real cause was
in **Staff Edit** (`staff_edit`): it lets you change anyone's `role`,
including someone who is currently a patient, but nothing deleted their old
`PatientProfile` row when that happened. So a person first registered as a
patient, then later switched to a staff role, kept an orphaned patient
record forever — invisible on the site's Patients list (which filters by
`role='patient'`), but still sitting in the database table.

## What changed

**1. The actual bug fix** — in `staff_edit`, right after a user's role is
saved, any leftover `PatientProfile` for that user is now deleted:

```python
# this person is now staff, so remove any old patient record they might still
# have (e.g. if they were first registered through "Register Patient" and are
# only now being made staff) - a person cannot be both at the same time
PatientProfile.objects.filter(user=user).delete()
```

**2. Data cleanup** — the one stale row (`PatientProfile` id=1, the
`pharmacist` test account) was deleted from the database.

**3. Model simplified for readability** — `StaffProfile` used to link to
`User` indirectly, through `UserProfile`:

```
User -> UserProfile -> StaffProfile   (old, 2 hops: profile.staff_profile)
User -> PatientProfile                (patient, 1 hop: user.patient_profile)
```

That asymmetry (staff take two hops, patients take one) was confusing and
was the main reason this app felt hard to follow. `StaffProfile` now links
straight to `User`, same as `PatientProfile`:

```
User -> StaffProfile     (new, 1 hop: user.staff_profile)
User -> PatientProfile   (unchanged, 1 hop: user.patient_profile)
```

Everywhere in the codebase that used to write `some_user.profile.staff_profile`
now writes `some_user.staff_profile`. Migrations
`0009_staffprofile_user` / `0010_migrate_staffprofile_user_data` /
`0011_staffprofile_drop_user_profile` carry existing rows across safely (add
new column → copy the data → drop the old column).

**4. Staff records are no longer created "late"** — before this fix,
`staff_add` only created the `User` + `UserProfile`; the `StaffProfile` row
(employee ID, department, etc) wasn't created until the first time someone
clicked Edit on that staff member. That's now inconsistent with how
`patient_add` always works (it creates everything up front), so `staff_add`
now creates the `StaffProfile` row immediately too, exactly like
`patient_add` does for `PatientProfile`.

## Where things live now

- `apps/user_management/models.py` — `StaffProfile.user` (was `user_profile`).
- `apps/user_management/views.py` — `staff_add`, `staff_edit`, `staff_detail`,
  `staff_user_list`, `doctor_room_list` all use `user.staff_profile`.
- `apps/appointment/views.py` (`_doctor_room`, `_doctor_fee`) and
  `apps/appointment/notifications.py` (`_room_for`) — both read a doctor's
  room/fee via `doctor.staff_profile...`, not `doctor.profile.staff_profile...`.
- `templates/dashboard/staff_management/staff_list.html` — reads
  `profile.user.staff_profile...` (the list is built from `UserProfile` rows,
  so it still needs the one hop from profile to user first).

## A rule for next time

A person's role (`UserProfile.role`) and their type-specific record
(`PatientProfile` or `StaffProfile`) can drift apart if role is ever changed
without also checking for the other kind of record. Any future code that
changes someone's role should follow the same pattern used in `staff_edit`:
delete the record type they no longer are.
