import streamlit as st
from supabase import create_client


class AuthService:
    def __init__(self):
        try:
            self.supabase = create_client(
                st.secrets["SUPABASE_URL"],
                st.secrets["SUPABASE_KEY"],
            )
            self._chat_message_text_column = None
            self._chat_sessions_has_title = None
        except Exception as e:
            raise Exception(f"Supabase initialization failed: {e}")

    # ---------------- SIGN UP ----------------
    def sign_up(self, name, email, password):
        try:
            response = self.supabase.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                }
            )

            if response.user:
                success, user_or_error = self._ensure_user_profile(
                    response.user, preferred_name=name
                )
                if success:
                    return True, user_or_error
                return False, user_or_error

            return False, "Signup failed"

        except Exception as e:
            return False, f"Sign up failed: {e}"

    # ---------------- LOGIN ----------------
    def sign_in(self, email, password):
        try:
            response = self.supabase.auth.sign_in_with_password(
                {
                    "email": email,
                    "password": password,
                }
            )

            if not response.user:
                return False, "Invalid login credentials"

            success, user_or_error = self._ensure_user_profile(response.user)
            if success:
                return True, user_or_error
            return False, user_or_error

        except Exception as e:
            return False, f"Login failed: {e}"

    # ---------------- VALIDATE SESSION TOKEN ----------------
    def validate_session_token(self):
        """
        Checks if a valid Supabase session exists.
        Used by SessionManager to keep the user logged in.
        """
        try:
            session_response = self.supabase.auth.get_session()

            # supabase-py response shape differs by version:
            # - older: object with .session
            # - newer: Session object directly
            active_session = getattr(session_response, "session", session_response)

            if active_session and getattr(active_session, "user", None):
                user = active_session.user

                success, user_or_error = self._ensure_user_profile(user)
                if success:
                    return user_or_error
                return None

            return None

        except Exception as e:
            print("Session validation error:", e)
            return None

    def _ensure_user_profile(self, auth_user, preferred_name=None):
        """
        Ensure a row exists in public.users with id == auth.users.id.
        This is required for RLS policies that use auth.uid() ownership checks.
        """
        try:
            auth_user_id = str(getattr(auth_user, "id", ""))
            auth_email = getattr(auth_user, "email", None)
            if not auth_user_id or not auth_email:
                return False, "Invalid auth user data"

            name = preferred_name or auth_email.split("@")[0]

            by_id = (
                self.supabase.table("users")
                .select("*")
                .eq("id", auth_user_id)
                .limit(1)
                .execute()
            )
            if by_id.data:
                return True, by_id.data[0]

            by_email = (
                self.supabase.table("users")
                .select("*")
                .eq("email", auth_email)
                .limit(1)
                .execute()
            )

            if by_email.data:
                existing = by_email.data[0]
                existing_id = str(existing.get("id", ""))
                if existing_id != auth_user_id:
                    migrated, migrated_or_error = self._migrate_legacy_user_id(
                        existing_id=existing_id,
                        auth_user_id=auth_user_id,
                        auth_email=auth_email,
                        name=(existing.get("name") or name),
                    )
                    if migrated:
                        return True, migrated_or_error

                    # Do not block login if migration fails; allow access with existing row.
                    print(f"User ID migration skipped: {migrated_or_error}")
                    return True, existing
                return True, existing

            created = (
                self.supabase.table("users")
                .insert(
                    {
                        "id": auth_user_id,
                        "email": auth_email,
                        "name": name,
                    }
                )
                .execute()
            )
            if created.data:
                return True, created.data[0]

            return False, "Failed to create user profile row"
        except Exception as e:
            return False, str(e)

    def _migrate_legacy_user_id(self, existing_id, auth_user_id, auth_email, name):
        """
        Migrate a legacy users.id to auth uid without violating FK constraints:
        1) Ensure target users row exists (temporary email),
        2) Repoint chat_sessions.user_id,
        3) Remove old users row,
        4) Normalize target users row email/name.
        """
        try:
            target_user = None

            by_target = (
                self.supabase.table("users")
                .select("*")
                .eq("id", auth_user_id)
                .limit(1)
                .execute()
            )
            if by_target.data:
                target_user = by_target.data[0]
            else:
                temp_email = f"{auth_email}.migrating.{auth_user_id[:8]}"
                created = (
                    self.supabase.table("users")
                    .insert(
                        {
                            "id": auth_user_id,
                            "email": temp_email,
                            "name": name,
                        }
                    )
                    .execute()
                )
                if created.data:
                    target_user = created.data[0]

            if not target_user:
                return False, "Could not create/find target user row for migration"

            self.supabase.table("chat_sessions").update({"user_id": auth_user_id}).eq(
                "user_id", existing_id
            ).execute()

            self.supabase.table("users").delete().eq("id", existing_id).execute()

            updated = (
                self.supabase.table("users")
                .update({"email": auth_email, "name": name})
                .eq("id", auth_user_id)
                .execute()
            )
            if updated.data:
                return True, updated.data[0]

            final_fetch = (
                self.supabase.table("users")
                .select("*")
                .eq("id", auth_user_id)
                .limit(1)
                .execute()
            )
            if final_fetch.data:
                return True, final_fetch.data[0]

            return False, "Migration completed partially but target profile not readable"
        except Exception as e:
            return False, str(e)

    # ---------------- LOGOUT ----------------
    def logout(self):
        try:
            self.supabase.auth.sign_out()
        except Exception as e:
            print("Logout error:", e)

    def sign_out(self):
        self.logout()

    # ---------------- SESSION MANAGEMENT ----------------
    def create_session(self, user_id, title="New Analysis Session"):
        try:
            session_response = self.supabase.auth.get_session()
            active_session = getattr(session_response, "session", session_response)
            auth_user = getattr(active_session, "user", None)
            if auth_user and getattr(auth_user, "id", None):
                user_id = str(auth_user.id)
            has_title = self._chat_sessions_has_title
            if has_title is None:
                has_title = self._detect_chat_sessions_has_title()

            payload = {"user_id": user_id}
            if has_title:
                payload["title"] = title

            try:
                result = self.supabase.table("chat_sessions").insert(payload).execute()
            except Exception as e:
                error_text = str(e).lower()
                if "title" in error_text and "chat_sessions" in error_text:
                    self._chat_sessions_has_title = False
                    result = self.supabase.table("chat_sessions").insert(
                        {"user_id": user_id}
                    ).execute()
                else:
                    raise

            if result.data:
                row = result.data[0]
                if "title" not in row or not row.get("title"):
                    row["title"] = title
                return True, row

            return False, "Unable to create session"
        except Exception as e:
            from services.app_logger import log_event

            log_event(
                "error",
                "create_session_failed",
                "Failed to create chat session",
                {"error": str(e)},
                user_id=user_id,
            )
            return False, str(e)

    def get_user_sessions(self, user_id):
        try:
            session_response = self.supabase.auth.get_session()
            active_session = getattr(session_response, "session", session_response)
            auth_user = getattr(active_session, "user", None)
            if auth_user and getattr(auth_user, "id", None):
                user_id = str(auth_user.id)

            result = (
                self.supabase.table("chat_sessions")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )
            sessions = result.data or []
            normalized = [self._normalize_session_row(s) for s in sessions]
            return True, normalized
        except Exception as e:
            return False, str(e)

    def delete_session(self, session_id):
        try:
            self.supabase.table("chat_messages").delete().eq(
                "session_id", session_id
            ).execute()
            self.supabase.table("chat_sessions").delete().eq("id", session_id).execute()
            return True, None
        except Exception as e:
            return False, str(e)

    def _normalize_session_row(self, session):
        if not isinstance(session, dict):
            return session

        if session.get("title"):
            return session

        created_at = session.get("created_at")
        if created_at:
            session["title"] = f"Session {str(created_at)[:10]}"
        else:
            session_id = str(session.get("id", ""))
            session["title"] = (
                f"Session {session_id[:8]}" if session_id else "Analysis Session"
            )
        return session

    # ---------------- SAVE CHAT ----------------
    def save_chat_message(self, session_id, message, role="user"):
        try:
            payload_base = {"session_id": session_id, "role": role}
            column_candidates = ["content", "message", "text", "body"]

            if self._chat_message_text_column:
                column_candidates = [self._chat_message_text_column] + [
                    c for c in column_candidates if c != self._chat_message_text_column
                ]

            for key in column_candidates:
                try:
                    payload = dict(payload_base)
                    payload[key] = message
                    self.supabase.table("chat_messages").insert(payload).execute()
                    self._chat_message_text_column = key
                    return True, None
                except Exception as e:
                    err = str(e).lower()
                    if (
                        "could not find" in err
                        and "column" in err
                        and "chat_messages" in err
                    ):
                        continue
                    from services.app_logger import log_event

                    log_event(
                        "error",
                        "save_chat_message_failed",
                        "Failed to save chat message",
                        {"error": str(e), "role": role},
                        user_id=st.session_state.get("user", {}).get("id"),
                        session_id=session_id,
                    )
                    return False, str(e)
            return (
                False,
                "chat_messages schema missing supported text column (expected one of: content, message, text, body)",
            )
        except Exception as e:
            from services.app_logger import log_event

            log_event(
                "error",
                "save_chat_message_exception",
                "Unhandled exception while saving chat message",
                {"error": str(e), "role": role},
                user_id=st.session_state.get("user", {}).get("id"),
                session_id=session_id,
            )
            return False, str(e)

    # ---------------- GET CHAT HISTORY ----------------
    def get_session_messages(self, session_id):
        try:
            result = (
                self.supabase.table("chat_messages")
                .select("*")
                .eq("session_id", session_id)
                .order("created_at")
                .execute()
            )
            rows = result.data or []
            normalized = [self._normalize_message_row(r) for r in rows]
            return True, normalized

        except Exception as e:
            from services.app_logger import log_event

            log_event(
                "error",
                "get_session_messages_failed",
                "Failed to fetch session messages",
                {"error": str(e)},
                user_id=st.session_state.get("user", {}).get("id"),
                session_id=session_id,
            )
            return False, str(e)

    def _normalize_message_row(self, row):
        if not isinstance(row, dict):
            return row

        if row.get("content") is not None:
            return row

        for key in ("message", "text", "body"):
            if row.get(key) is not None:
                row["content"] = row.get(key)
                return row

        row["content"] = ""
        return row

    def _detect_chat_sessions_has_title(self):
        try:
            self.supabase.table("chat_sessions").select("title").limit(1).execute()
            self._chat_sessions_has_title = True
        except Exception:
            self._chat_sessions_has_title = False
        return self._chat_sessions_has_title
