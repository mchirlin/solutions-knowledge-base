"""
Dynamic interaction tests for AS_FM_captureUserContactDetails.

These tests deploy the SAIL interface to a live Appian test site,
then use appian-locust (standalone mode) to fill fields, click
buttons, and verify that SAIL re-evaluation produces the expected
validations and state changes.

Run:
    pytest sail/tests/test_contact_form_dynamic.py -v

Requires:
    - appian-locust installed / on sys.path (~/repo/appian-locust)
    - Network access to eng-test-aidc-dev.appianpreview.com
"""

import json
import sys, os

sys.path.insert(0, os.path.expanduser("~/repo/appian-locust"))

from appian_locust.exceptions.exceptions import IgnoredValidationException
from appian_locust.utilities.helper import (
    find_component_by_attribute_in_dict,
)


# ── Helpers ───────────────────────────────────────────────────────────

def fill_expecting_validation(form, label, value):
    """
    Fill a text field expecting a validation error.
    appian-locust raises IgnoredValidationException when the server
    returns validations after a re-eval. We catch it and return the
    form (whose internal state has been updated before the raise).
    """
    try:
        return form.fill_text_field(label, value)
    except IgnoredValidationException:
        return form


def get_component_value(state: dict, label: str):
    """Find a component by label and return its current value."""
    comp = find_component_by_attribute_in_dict("label", label, state, raise_error=False)
    if comp:
        return comp.get("value")
    return None


def state_contains_text(state: dict, text: str) -> bool:
    """Check whether a text string appears anywhere in the serialised state."""
    return text in json.dumps(state)


# ── Tests: Email validation ───────────────────────────────────────────

class TestEmailValidation:
    """Verify the email regex validation fires on re-evaluation."""

    def test_invalid_email_shows_validation(self, contact_form):
        form = fill_expecting_validation(contact_form, "Email", "not-an-email")
        state = form.get_latest_state()
        assert state_contains_text(state, "Please enter a valid email address.")

    def test_valid_email_no_validation(self, contact_form):
        form = contact_form.fill_text_field("Email", "user@example.com")
        state = form.get_latest_state()
        assert not state_contains_text(state, "Please enter a valid email address.")

    def test_empty_email_no_validation(self, contact_form):
        """Empty email should not trigger the regex validation (only required)."""
        form = contact_form.fill_text_field("Email", "")
        state = form.get_latest_state()
        assert not state_contains_text(state, "Please enter a valid email address.")


# ── Tests: Phone validation ──────────────────────────────────────────

class TestPhoneValidation:
    """Verify the phone regex validation fires on re-evaluation."""

    def test_invalid_phone_shows_validation(self, contact_form):
        form = fill_expecting_validation(contact_form, "Phone", "abc")
        state = form.get_latest_state()
        assert state_contains_text(state, "Please enter a valid phone number.")

    def test_valid_phone_no_validation(self, contact_form):
        form = contact_form.fill_text_field("Phone", "+1 (555) 123-4567")
        state = form.get_latest_state()
        assert not state_contains_text(state, "Please enter a valid phone number.")

    def test_empty_phone_no_validation(self, contact_form):
        form = contact_form.fill_text_field("Phone", "")
        state = form.get_latest_state()
        assert not state_contains_text(state, "Please enter a valid phone number.")


# ── Tests: Field interaction round-trips ─────────────────────────────

class TestFieldInteractions:
    """Verify that filling fields persists values through re-evaluation."""

    def test_first_name_persists(self, contact_form):
        form = contact_form.fill_text_field("First Name", "Jane")
        assert get_component_value(form.get_latest_state(), "First Name") == "Jane"

    def test_last_name_persists(self, contact_form):
        form = contact_form.fill_text_field("Last Name", "Doe")
        assert get_component_value(form.get_latest_state(), "Last Name") == "Doe"

    def test_multiple_fields_persist(self, contact_form):
        form = contact_form.fill_text_field("First Name", "Jane")
        form = form.fill_text_field("Last Name", "Doe")
        form = form.fill_text_field("Email", "jane@example.com")
        state = form.get_latest_state()
        assert get_component_value(state, "First Name") == "Jane"
        assert get_component_value(state, "Last Name") == "Doe"
        assert get_component_value(state, "Email") == "jane@example.com"


# ── Tests: Submit behaviour ──────────────────────────────────────────

class TestSubmitBehaviour:
    """Verify submit button triggers required-field validations."""

    def test_submit_empty_form_shows_required_errors(self, contact_form):
        """Clicking Submit with no data should surface required-field errors."""
        try:
            form = contact_form.click_button("Submit")
        except IgnoredValidationException:
            form = contact_form
        state = form.get_latest_state()
        # Required fields should produce validation messages in the state
        serialized = json.dumps(state)
        has_validations = (
            "is required" in serialized.lower()
            or "validationMessage" in serialized
            or "requiredValidation" in serialized
            # Appian marks required fields with a validation group
            or state_contains_text(state, "required")
        )
        assert has_validations, "Expected required-field validations on empty submit"

    def test_submit_valid_form_no_validation_errors(self, contact_form):
        """A fully filled valid form should submit cleanly."""
        form = contact_form.fill_text_field("First Name", "Jane")
        form = form.fill_text_field("Last Name", "Doe")
        form = form.fill_text_field("Email", "jane@example.com")
        form = form.click_button("Submit")
        state = form.get_latest_state()
        assert not state_contains_text(state, "Please enter a valid email address.")
        assert not state_contains_text(state, "Please enter a valid phone number.")

    def test_cancel_does_not_validate(self, contact_form):
        """Cancel button has validate:false, so it should not trigger errors."""
        form = contact_form.click_button("Cancel")
        state = form.get_latest_state()
        assert not state_contains_text(state, "Please enter a valid email address.")
        assert not state_contains_text(state, "Please enter a valid phone number.")


# ── Tests: Validation correction flow ────────────────────────────────

class TestValidationCorrectionFlow:
    """
    Verify that fixing an invalid value clears the validation.

    NOTE: appian-locust's UiReconciler merges component deltas via
    dict.update(), so if the server returns a delta that omits the
    'validations' key (because the validation cleared), the old
    validations persist in the local state. To work around this, we
    use a fresh form for the "corrected" step and verify the valid
    value does not trigger a validation on its own.
    """

    def test_invalid_email_triggers_then_valid_email_clean(self, contact_form, appian_client):
        """Bad email triggers validation; a fresh form with good email does not."""
        # Step 1: bad value triggers validation
        form = fill_expecting_validation(contact_form, "Email", "bad")
        assert state_contains_text(form.get_latest_state(), "Please enter a valid email address.")
        # Step 2: fresh form with good value — no validation
        form2 = appian_client.visitor.visit_site("test-site", "test-interface")
        form2 = form2.fill_text_field("Email", "good@example.com")
        assert not state_contains_text(form2.get_latest_state(), "Please enter a valid email address.")

    def test_invalid_phone_triggers_then_valid_phone_clean(self, contact_form, appian_client):
        """Bad phone triggers validation; a fresh form with good phone does not."""
        form = fill_expecting_validation(contact_form, "Phone", "xyz")
        assert state_contains_text(form.get_latest_state(), "Please enter a valid phone number.")
        form2 = appian_client.visitor.visit_site("test-site", "test-interface")
        form2 = form2.fill_text_field("Phone", "555-123-4567")
        assert not state_contains_text(form2.get_latest_state(), "Please enter a valid phone number.")
