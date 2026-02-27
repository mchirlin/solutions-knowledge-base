/*
 * Tests for: AS_FM_captureUserContactDetails
 *
 * These test expressions validate the regex patterns and logic
 * used in the contact form. Each test can be evaluated
 * independently via the SAIL expression evaluator.
 */


/* ═══════════════════════════════════════════════════════════════════════
 * TEST 1: Email Validation — Valid Addresses
 * Expected: all results should be true
 * ═══════════════════════════════════════════════════════════════════════ */
a!localVariables(
  local!pattern: "^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+[.][A-Za-z]{2,}$",
  local!testCases: {
    "user@example.com",
    "first.last@company.org",
    "name+tag@sub.domain.co.uk",
    "test123@test.io"
  },
  a!forEach(
    items: local!testCases,
    expression: a!map(
      input: fv!item,
      result: regexmatch(local!pattern, fv!item),
      expected: true,
      pass: regexmatch(local!pattern, fv!item) = true
    )
  )
)


/* ═══════════════════════════════════════════════════════════════════════
 * TEST 2: Email Validation — Invalid Addresses
 * Expected: all results should be false
 * ═══════════════════════════════════════════════════════════════════════ */
a!localVariables(
  local!pattern: "^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+[.][A-Za-z]{2,}$",
  local!testCases: {
    "not-an-email",
    "@missing-local.com",
    "missing-domain@",
    "spaces in@email.com",
    "double@@at.com"
  },
  a!forEach(
    items: local!testCases,
    expression: a!map(
      input: fv!item,
      result: regexmatch(local!pattern, fv!item),
      expected: false,
      pass: regexmatch(local!pattern, fv!item) = false
    )
  )
)


/* ═══════════════════════════════════════════════════════════════════════
 * TEST 3: Phone Validation — Valid Numbers
 * Expected: all results should be true
 * ═══════════════════════════════════════════════════════════════════════ */
a!localVariables(
  local!pattern: "^[+]?[0-9 ()-]{7,20}$",
  local!testCases: {
    "+1 (555) 123-4567",
    "555-123-4567",
    "(555) 1234567",
    "+44 20 7946 0958",
    "1234567"
  },
  a!forEach(
    items: local!testCases,
    expression: a!map(
      input: fv!item,
      result: regexmatch(local!pattern, fv!item),
      expected: true,
      pass: regexmatch(local!pattern, fv!item) = true
    )
  )
)


/* ═══════════════════════════════════════════════════════════════════════
 * TEST 4: Phone Validation — Invalid Numbers
 * Expected: all results should be false
 * ═══════════════════════════════════════════════════════════════════════ */
a!localVariables(
  local!pattern: "^[+]?[0-9 ()-]{7,20}$",
  local!testCases: {
    "abc",
    "12345",
    "phone: 555-1234",
    "++1234567890"
  },
  a!forEach(
    items: local!testCases,
    expression: a!map(
      input: fv!item,
      result: regexmatch(local!pattern, fv!item),
      expected: false,
      pass: regexmatch(local!pattern, fv!item) = false
    )
  )
)


/* ═══════════════════════════════════════════════════════════════════════
 * TEST 5: Null/Empty Handling — Validations should not fire on empty
 * Expected: empty validations list (no error messages)
 * ═══════════════════════════════════════════════════════════════════════ */
a!localVariables(
  local!emailEmpty: null,
  local!phoneEmpty: null,
  local!emailValidation: if(
    a!isNullOrEmpty(local!emailEmpty),
    {},
    if(
      not(regexmatch("^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+[.][A-Za-z]{2,}$", local!emailEmpty)),
      "Please enter a valid email address.",
      {}
    )
  ),
  local!phoneValidation: if(
    a!isNullOrEmpty(local!phoneEmpty),
    {},
    if(
      not(regexmatch("^[+]?[0-9 ()-]{7,20}$", local!phoneEmpty)),
      "Please enter a valid phone number.",
      {}
    )
  ),
  a!map(
    emailValidation: local!emailValidation,
    phoneValidation: local!phoneValidation,
    emailPass: local!emailValidation = {},
    phonePass: local!phoneValidation = {}
  )
)


/* ═══════════════════════════════════════════════════════════════════════
 * TEST 6: Consent Checkbox Logic
 * Expected: consentGiven toggles correctly based on checkbox selection
 * ═══════════════════════════════════════════════════════════════════════ */
a!localVariables(
  local!selectedTrue: { true },
  local!selectedEmpty: {},
  local!consentWhenChecked: if(length(local!selectedTrue) > 0, true, false),
  local!consentWhenUnchecked: if(length(local!selectedEmpty) > 0, true, false),
  a!map(
    checkedResult: local!consentWhenChecked,
    checkedPass: local!consentWhenChecked = true,
    uncheckedResult: local!consentWhenUnchecked,
    uncheckedPass: local!consentWhenUnchecked = false
  )
)


/* ═══════════════════════════════════════════════════════════════════════
 * TEST 7: Subject Dropdown Values
 * Expected: all choice values are non-null and unique
 * ═══════════════════════════════════════════════════════════════════════ */
a!localVariables(
  local!choiceValues: {
    "general",
    "support",
    "sales",
    "partnership",
    "feedback",
    "other"
  },
  local!uniqueCount: length(union(local!choiceValues, local!choiceValues)),
  a!map(
    totalValues: length(local!choiceValues),
    uniqueValues: local!uniqueCount,
    allUnique: length(local!choiceValues) = local!uniqueCount,
    pass: length(local!choiceValues) = local!uniqueCount
  )
)


/* ═══════════════════════════════════════════════════════════════════════
 * TEST 8: Full Interface Render — Smoke Test
 * Expected: status 200, interface renders without errors
 * Validate this expression via the evaluate-sail API.
 * ═══════════════════════════════════════════════════════════════════════ */
a!localVariables(
  local!contact: a!map(
    firstName: null,
    lastName: null,
    email: null,
    phone: null,
    subject: null,
    message: null
  ),
  local!isSubmitted: false,
  local!consentGiven: false,
  a!formLayout(
    label: "Contact Us",
    contents: {
      a!columnsLayout(
        columns: {
          a!columnLayout(
            contents: {
              a!textField(
                label: "First Name",
                labelPosition: "ABOVE",
                value: local!contact.firstName,
                saveInto: local!contact.firstName,
                required: true,
                characterLimit: 100
              ),
              a!textField(
                label: "Email",
                labelPosition: "ABOVE",
                value: local!contact.email,
                saveInto: local!contact.email,
                required: true,
                characterLimit: 250,
                validations: if(
                  a!isNullOrEmpty(local!contact.email),
                  {},
                  if(
                    not(
                      regexmatch(
                        "^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+[.][A-Za-z]{2,}$",
                        local!contact.email
                      )
                    ),
                    "Please enter a valid email address.",
                    {}
                  )
                )
              ),
              a!dropdownField(
                label: "Subject",
                labelPosition: "ABOVE",
                placeholder: "Select a subject...",
                choiceLabels: {
                  "General Inquiry",
                  "Technical Support",
                  "Sales",
                  "Partnership",
                  "Feedback",
                  "Other"
                },
                choiceValues: {
                  "general",
                  "support",
                  "sales",
                  "partnership",
                  "feedback",
                  "other"
                },
                value: local!contact.subject,
                saveInto: local!contact.subject,
                required: true
              )
            }
          ),
          a!columnLayout(
            contents: {
              a!textField(
                label: "Last Name",
                labelPosition: "ABOVE",
                value: local!contact.lastName,
                saveInto: local!contact.lastName,
                required: true,
                characterLimit: 100
              ),
              a!textField(
                label: "Phone",
                labelPosition: "ABOVE",
                value: local!contact.phone,
                saveInto: local!contact.phone,
                characterLimit: 20,
                validations: if(
                  a!isNullOrEmpty(local!contact.phone),
                  {},
                  if(
                    not(
                      regexmatch(
                        "^[+]?[0-9 ()-]{7,20}$",
                        local!contact.phone
                      )
                    ),
                    "Please enter a valid phone number.",
                    {}
                  )
                )
              )
            }
          )
        }
      ),
      a!paragraphField(
        label: "Message",
        labelPosition: "ABOVE",
        value: local!contact.message,
        saveInto: local!contact.message,
        required: true,
        height: "SHORT",
        characterLimit: 4000
      ),
      a!checkboxField(
        labelPosition: "COLLAPSED",
        choiceLabels: { "I agree to the privacy policy and consent to being contacted." },
        choiceValues: { true },
        value: if(local!consentGiven, { true }, {}),
        saveInto: {
          a!save(
            local!consentGiven,
            if(length(save!value) > 0, true, false)
          )
        }
      )
    },
    buttons: a!buttonLayout(
      primaryButtons: {
        a!buttonWidget(
          label: "Send Message",
          accessibilityText: "Submit your contact form",
          submit: true,
          style: "SOLID",
          validate: true
        )
      },
      secondaryButtons: {
        a!buttonWidget(
          label: "Cancel",
          style: "OUTLINE",
          submit: true,
          validate: false,
          value: true,
          saveInto: local!isSubmitted
        )
      }
    )
  )
)
