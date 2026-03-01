__version__ = "0.1.0"


def _patch_session_resume_for_invalid_user():
	"""If session has no user (None/empty), treat as invalid and start as Guest instead of throwing."""
	import frappe
	from frappe.auth import clear_cookies
	from frappe.sessions import Session, delete_session

	_original_resume = Session.resume

	def resume(self):
		data = self.get_session_record()
		if data and (data.get("user") is None or data.get("user") == ""):
			# Invalid session: no user. Delete it, clear cookie, start as Guest.
			try:
				delete_session(self.sid, reason="Invalid session (no user)")
			except Exception:
				pass
			clear_cookies()
			self.sid = "Guest"
			data = self.get_session_data()
			if data:
				self.data.update({"data": data, "user": data.user, "sid": self.sid})
				self.user = data.user
			else:
				self.start_as_guest()
			if self.sid != "Guest":
				frappe.local.user_lang = frappe.translate.get_user_lang(self.data.user)
				frappe.local.lang = frappe.local.user_lang
			return
		_original_resume(self)

	Session.resume = resume


# Apply patch when app is loaded (handles "User None is disabled" from bad session cookies)
try:
	_patch_session_resume_for_invalid_user()
except Exception:
	pass  # Don't break app load if patch fails
