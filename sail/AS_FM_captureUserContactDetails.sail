/*
 * Interface: AS_FM_captureUserContactDetails
 *
 * A styled account-creation / contact-details form inspired by a
 * dark-themed split-panel design.  Left panel shows branding and a
 * hero message; right panel contains the form fields.
 *
 * Fields:
 *   - First Name (required)
 *   - Last Name (required)
 *   - Email (required, regex validated)
 *   - Phone (optional, regex validated)
 *   - Organization (optional)
 *   - Role / Title (optional)
 *   - Notes (optional, paragraph)
 */
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

  /* ── Colour tokens ── */
  local!darkNavy:  "#1B3A4B",
  local!gold:      "#C9A96E",
  local!white:     "#FFFFFF",
  local!lightGrey: "#F5F5F5",

  a!headerContentLayout(
    header: {},
    contents: {
      a!cardLayout(
        contents: {
          a!columnsLayout(
            columns: {
              /* ═══════════════════════════════════════════
                 LEFT PANEL – Branding / Hero
                 ═══════════════════════════════════════════ */
              a!columnLayout(
                width: "MEDIUM",
                contents: {
                  a!cardLayout(
                    contents: {
                      a!richTextDisplayField(
                        labelPosition: "COLLAPSED",
                        value: {
                          a!richTextItem(
                            text: char(10) & char(10),
                            size: "MEDIUM"
                          )
                        }
                      ),

                      /* Gold accent bar */
                      a!cardLayout(
                        contents: {},
                        height: "EXTRA_SHORT",
                        style: "NONE",
                        backgroundColor: local!gold,
                        marginBelow: "STANDARD",
                        showBorder: false
                      ),

                      a!richTextDisplayField(
                        labelPosition: "COLLAPSED",
                        value: {
                          a!richTextItem(
                            text: "CO.",
                            size: "LARGE",
                            style: "STRONG",
                            color: local!gold
                          )
                        },
                        marginBelow: "STANDARD"
                      ),

                      /* Hero headline */
                      a!richTextDisplayField(
                        labelPosition: "COLLAPSED",
                        value: {
                          a!richTextItem(
                            text: "Let's Make" & char(10) & "it Happen" & char(10) & "Together!",
                            size: "LARGE",
                            style: "STRONG",
                            color: local!white
                          )
                        },
                        marginBelow: "STANDARD"
                      ),

                      /* Decorative circle (stamp) */
                      a!stampField(
                        labelPosition: "COLLAPSED",
                        icon: "USER",
                        backgroundColor: local!darkNavy,
                        contentColor: local!lightGrey,
                        size: "LARGE",
                        align: "CENTER",
                        marginBelow: "STANDARD"
                      ),

                      a!richTextDisplayField(
                        labelPosition: "COLLAPSED",
                        value: {
                          a!richTextItem(
                            text: char(10),
                            size: "MEDIUM"
                          )
                        }
                      )
                    },
                    style: "NONE",
                    backgroundColor: local!darkNavy,
                    padding: "STANDARD",
                    marginBelow: "NONE",
                    showBorder: false
                  )
                }
              ),

              /* ═══════════════════════════════════════════
                 RIGHT PANEL – Form
                 ═══════════════════════════════════════════ */
              a!columnLayout(
                width: "WIDE",
                contents: {
                  a!cardLayout(
                    contents: {
                      /* Sign-in link */
                      a!richTextDisplayField(
                        labelPosition: "COLLAPSED",
                        value: {
                          a!richTextItem(
                            text: "Already have an account? ",
                            color: "SECONDARY"
                          ),
                          a!richTextItem(
                            text: "Sign in here!",
                            link: a!dynamicLink(value: true, saveInto: local!isSubmitted),
                            linkStyle: "STANDALONE",
                            color: local!gold
                          )
                        },
                        align: "RIGHT",
                        marginBelow: "STANDARD"
                      ),

                      /* Form heading */
                      a!richTextDisplayField(
                        labelPosition: "COLLAPSED",
                        value: {
                          a!richTextItem(
                            text: "Create An Account",
                            size: "LARGE",
                            style: "STRONG",
                            color: local!white
                          )
                        },
                        marginBelow: "STANDARD"
                      ),

                      /* ── Row 1: First Name / Last Name ── */
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
                                characterLimit: 100,
                                placeholder: "First Name"
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
                                characterLimit: 100,
                                placeholder: "Last Name"
                              )
                            }
                          )
                        }
                      ),

                      /* ── Row 2: Email / Phone ── */
                      a!columnsLayout(
                        columns: {
                          a!columnLayout(
                            contents: {
                              a!textField(
                                label: "Email",
                                labelPosition: "ABOVE",
                                value: local!contact.email,
                                saveInto: local!contact.email,
                                required: true,
                                characterLimit: 254,
                                placeholder: "email@example.com",
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
                              )
                            }
                          ),
                          a!columnLayout(
                            contents: {
                              a!textField(
                                label: "Phone",
                                labelPosition: "ABOVE",
                                value: local!contact.phone,
                                saveInto: local!contact.phone,
                                characterLimit: 20,
                                placeholder: "+1 (555) 123-4567",
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

                      /* ── Row 3: Organization / Role ── */
                      a!columnsLayout(
                        columns: {
                          a!columnLayout(
                            contents: {
                              a!textField(
                                label: "Organization",
                                labelPosition: "ABOVE",
                                value: local!contact.organization,
                                saveInto: local!contact.organization,
                                characterLimit: 200,
                                placeholder: "Company name"
                              )
                            }
                          ),
                          a!columnLayout(
                            contents: {
                              a!textField(
                                label: "Role / Title",
                                labelPosition: "ABOVE",
                                value: local!contact.roleTitle,
                                saveInto: local!contact.roleTitle,
                                characterLimit: 150,
                                placeholder: "Your role"
                              )
                            }
                          )
                        }
                      ),

                      /* ── Notes ── */
                      a!paragraphField(
                        label: "Notes",
                        labelPosition: "ABOVE",
                        value: local!contact.notes,
                        saveInto: local!contact.notes,
                        height: "SHORT",
                        characterLimit: 1000,
                        placeholder: "Any additional information..."
                      ),

                      /* ── Submit button (gold-styled) ── */
                      a!buttonLayout(
                        primaryButtons: {
                          a!buttonWidget(
                            label: "Submit",
                            submit: true,
                            style: "SOLID",
                            validate: true,
                            width: "FILL"
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
                      ),

                      /* ── Footer ── */
                      a!richTextDisplayField(
                        labelPosition: "COLLAPSED",
                        value: {
                          a!richTextItem(
                            text: char(169) & " 2026 Company Inc Ltd.",
                            size: "SMALL",
                            color: "SECONDARY"
                          )
                        },
                        align: "CENTER",
                        marginAbove: "STANDARD"
                      )
                    },
                    style: "NONE",
                    backgroundColor: local!darkNavy,
                    padding: "STANDARD",
                    marginBelow: "NONE",
                    showBorder: false
                  )
                }
              )
            },
            spacing: "NONE"
          )
        },
        style: "NONE",
        padding: "NONE",
        marginBelow: "NONE",
        showBorder: false
      )
    },
    backgroundColor: local!darkNavy
  )
)
