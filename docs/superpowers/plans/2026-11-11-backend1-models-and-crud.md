# Backend 1: Models, Migrations, Admin & Ticket CRUD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the database models (`Role`, `UserProfile`, `Ticket`, `Comment`, `TicketHistory`), migrations, Django admin configuration, and real CRUD & ticket lifecycle views for Dev BackEnd 1 (Gia Bảo), transitioning from the temporary demo store to persistent database storage.

**Architecture:** Use Django standard models extending `auth.User` via a OneToOne `UserProfile` and `Role`. Implement `Ticket`, `Comment`, and `TicketHistory` in `tickets.models` matching the provided Class Diagram and relational schema. Wire views in `tickets.views` to query the real database while keeping frontend template and form contracts intact.

**Tech Stack:** Python 3.10+, Django 6.1+, SQLite / MySQL compatible ORM.

**Spec:** `de_tai.docx` (ĐỀ TÀI NHÓM 2: Hệ thống tiếp nhận và xử lý sự cố mạng helpdesk) and the provided Class/ER diagrams.

## Global Constraints
- Python 3.10+ / Django 6.1+
- Template contracts from `FRONTEND1.md` must be preserved: ticket codes formatted as `HD-<id>`, categories (`network`, `vpn`, `printer`, `other`), priorities (`low`, `normal`, `high`, `urgent`), statuses (`new`, `in_progress`, `resolved`, `closed`).
- Attachment validation rules in `tickets/attachment_validators.py` and `forms.py` must remain functional.
- Pass existing tests in `accounts`, `kb`, and `tickets`.

## Review Focus
1. User role checks: `is_admin()`, `is_technician()`, `is_end_user()` should handle missing UserProfile gracefully without crashing.
2. Permission isolation: Regular users must only see their own tickets; technicians and admins can see all assigned or department tickets.
3. Ticket status transitions: Changing status or assigning technicians must automatically create a `TicketHistory` entry.
4. Comments on closed tickets: Users must not be allowed to comment on tickets with status `closed`.
5. Display formatting: `steps`, `status_label`, `category_label`, `priority_label`, `code` must match template expectations.

---

### Task 1: Accounts Models (`Role`, `UserProfile`) and Admin

**Files:**
- Create: `accounts/tests_models.py`
- Modify: `accounts/models.py`
- Modify: `accounts/admin.py`

**Interfaces:**
- Produces:
  - `Role(id, name, description)`
  - `UserProfile(id, user, role, phone, department)`
  - Methods on `UserProfile`: `is_admin() -> bool`, `is_technician() -> bool`, `is_end_user() -> bool`

- [ ] **Step 1: Write tests for `Role` and `UserProfile`**
- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement `Role` and `UserProfile` in `accounts/models.py`**
- [ ] **Step 4: Register models in `accounts/admin.py`**
- [ ] **Step 5: Run makemigrations accounts and verify tests pass**

---

### Task 2: Tickets Models (`Ticket`, `Comment`, `TicketHistory`) and Admin

**Files:**
- Create: `tickets/test_models.py`
- Modify: `tickets/models.py`
- Modify: `tickets/admin.py`

**Interfaces:**
- Produces:
  - `Ticket(id, title, category, priority, location, description, status, created_by, assigned_to, created_at, updated_at)`
  - `Comment(id, ticket, user, content, created_at)`
  - `TicketHistory(id, ticket, changed_by, old_status, new_status, assigned_to, note, created_at)`
  - Methods on `Ticket`: `get_code() -> str`, `assign_technician(tech, by, note=None)`, `change_status(new_status, by, note=None)`, `can_view(user) -> bool`

- [ ] **Step 1: Write tests for `Ticket`, `Comment`, `TicketHistory`**
- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement models and helper methods in `tickets/models.py`**
- [ ] **Step 4: Register models in `tickets/admin.py`**
- [ ] **Step 5: Run makemigrations tickets and verify tests pass**

---

### Task 3: Database Migrations and Default Role Seeding

**Files:**
- Modify: `accounts/migrations/0001_initial.py`
- Modify: `tickets/migrations/0001_initial.py`

- [ ] **Step 1: Run `python manage.py migrate`**
- [ ] **Step 2: Add post_migrate or helper to initialize default Roles (`admin`, `technician`, `user`)**

---

### Task 4: Connect Real Models to Views & Forms in `tickets/`

**Files:**
- Modify: `tickets/views.py`
- Modify: `tickets/forms.py` (if needed for ModelForm or keeping TicketForm compatible)
- Modify: `tickets/tests.py`

- [ ] **Step 1: Adapt `ticket_create` to save `Ticket` to DB and log `TicketHistory`**
- [ ] **Step 2: Adapt `ticket_list` to query DB with search, filter, pagination, and user permissions**
- [ ] **Step 3: Adapt `ticket_detail` to display ticket details, comments, history, and accept new comments**
- [ ] **Step 4: Adapt `home` view to compute real statistics and show recent tickets**
- [ ] **Step 5: Add technician assignment / status update view for IT support / admin**
- [ ] **Step 6: Run tests and ensure all pass**

---

### Task 5: Final Verification and Documentation

- [ ] **Step 1: Run full test suite (`python manage.py test`)**
- [ ] **Step 2: Verify Django checks (`python manage.py check`)**
- [ ] **Step 3: Update documentation and handoff for teammates**

