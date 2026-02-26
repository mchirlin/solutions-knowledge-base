/*
 * Tests for: AS_FM_captureUserContactDetails
 *
 * These test expressions validate the regex patterns and logic
 * used in the contact details form. Each test can be evaluated
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
 * TEST 6: Full Interface Render — Smoke Test
 * Expected: status 200, interface renders without errors
 * Validate this expression via the evaluate-sail API.
 * ═══════════════════════════════════════════════════════════════════════ */
a!localVariables(
  local!contact: a!map(
    firstName: null,
    lastName: null,
    email: null,
    phone: null,
    organization: null,
    roleTitle: null,
    notes: null
  ),
  local!isSubmitted: false,
  a!formLayout(
    label: "User Contact Details",
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
                characterLimit: 254,
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
              a!textField(
                label: "Organization",
                labelPosition: "ABOVE",
                value: local!contact.organization,
                saveInto: local!contact.organization,
                characterLimit: 200
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
              ),
              a!textField(
                label: "Role / Title",
                labelPosition: "ABOVE",
                value: local!contact.roleTitle,
                saveInto: local!contact.roleTitle,
                characterLimit: 150
              )
            }
          )
        }
      ),
      a!paragraphField(
        label: "Notes",
        labelPosition: "ABOVE",
        value: local!contact.notes,
        saveInto: local!contact.notes,
        height: "MEDIUM",
        characterLimit: 1000
      )
    },
    buttons: a!buttonLayout(
      primaryButtons: {
        a!buttonWidget(
          label: "Submit",
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
