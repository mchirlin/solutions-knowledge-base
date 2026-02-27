/*
 * Interface: AS_FM_captureUserContactDetails
 *
 * A styled contact form for a website, using a dark-themed split-panel
 * layout. Left panel shows branding with a hero message and decorative
 * elements. Right panel contains the contact form fields with validation.
 *
 * Fields: First Name, Last Name, Email, Phone, Subject (dropdown),
 *         Message, and a consent checkbox.
 *
 * NOTE: a!richTextItem is avoided because the evaluation API cannot
 *       resolve env!features. Plain string values and a!stampField /
 *       a!imageField are used for visual elements instead.
 *
 * NOTE: a!cardLayout CANNOT be a direct child inside a!columnLayout
 *       within a!columnsLayout — it causes a runtime error. Instead,
 *       the dark background comes from a!headerContentLayout's
 *       backgroundColor, and a single outer a!cardLayout wraps the
 *       entire columnsLayout.
 */
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
                  /* Accent bar */
                  a!stampField(
                    labelPosition: "COLLAPSED",
                    icon: "square",
                    backgroundColor: "#C9A96E",
                    contentColor: "#C9A96E",
                    size: "TINY",
                    align: "START",
                    marginBelow: "MORE"
                  ),

                  /* Hero headline */
                  a!richTextDisplayField(
                    labelPosition: "COLLAPSED",
                    value: "Get In Touch With Us",
                    marginBelow: "STANDARD"
                  ),

                  /* Subtext */
                  a!richTextDisplayField(
                    labelPosition: "COLLAPSED",
                    value: "We would love to hear from you. Fill out the form and our team will get back to you within 24 hours.",
                    marginBelow: "MORE"
                  ),

                  /* Decorative envelope icon */
                  a!stampField(
                    labelPosition: "COLLAPSED",
                    icon: "ENVELOPE",
                    backgroundColor: "#2C5060",
                    contentColor: "#8AACB8",
                    size: "LARGE",
                    align: "CENTER",
                    marginBelow: "STANDARD"
                  ),

                  /* Contact info hints */
                  a!richTextDisplayField(
                    labelPosition: "COLLAPSED",
                    value: "support@example.com",
                    align: "CENTER",
                    marginBelow: "EVEN_LESS"
                  ),

                  a!richTextDisplayField(
                    labelPosition: "COLLAPSED",
                    value: "+1 (555) 000-0000",
                    align: "CENTER",
                    marginBelow: "STANDARD"
                  )
                }
              ),

              /* ═══════════════════════════════════════════
                 RIGHT PANEL – Contact Form
                 ═══════════════════════════════════════════ */
              a!columnLayout(
                width: "WIDE",
                contents: {
                  /* Form heading */
                  a!richTextDisplayField(
                    labelPosition: "COLLAPSED",
                    value: "Contact Us",
                    marginBelow: "STANDARD"
                  ),

                  /* ── Row 1: First Name / Last Name ── */
                  a!sideBySideLayout(
                    items: {
                      a!sideBySideItem(
                        item: a!textField(
                          label: "First Name",
                          labelPosition: "ABOVE",
                          value: local!contact.firstName,
                          saveInto: local!contact.firstName,
                          required: true,
                          characterLimit: 100,
                          placeholder: "First Name"
                        )
                      ),
                      a!sideBySideItem(
                        item: a!textField(
                          label: "Last Name",
                          labelPosition: "ABOVE",
                          value: local!contact.lastName,
                          saveInto: local!contact.lastName,
                          required: true,
                          characterLimit: 100,
                          placeholder: "Last Name"
                        )
                      )
                    }
                  ),

                  /* ── Row 2: Email / Phone ── */
                  a!sideBySideLayout(
                    items: {
                      a!sideBySideItem(
                        item: a!textField(
                          label: "Email",
                          labelPosition: "ABOVE",
                          value: local!contact.email,
                          saveInto: local!contact.email,
                          required: true,
                          characterLimit: 250,
                          placeholder: "you@example.com",
                          validations: if(
                            a!isNullOrEmpty(local!contact.email),
                            {},
                            if(
                              not(
                                regexMatch(
                                  pattern: "^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$",
                                  value: local!contact.email
                                )
                              ),
                              { "Please enter a valid email address." },
                              {}
                            )
                          )
                        )
                      ),
                      a!sideBySideItem(
                        item: a!textField(
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
                                regexMatch(
                                  pattern: "^[+]?[0-9 ()-]{7,20}$",
                                  value: local!contact.phone
                                )
                              ),
                              { "Please enter a valid phone number." },
                              {}
                            )
                          )
                        )
                      )
                    }
                  ),

                  /* ── Subject dropdown ── */
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
                  ),

                  /* ── Message ── */
                  a!paragraphField(
                    label: "Message",
                    labelPosition: "ABOVE",
                    value: local!contact.message,
                    saveInto: local!contact.message,
                    required: true,
                    characterLimit: 4000,
                    placeholder: "How can we help you?",
                    height: "SHORT"
                  ),

                  /* ── Consent checkbox ── */
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
                    },
                    validations: if(
                      not(local!consentGiven),
                      { "You must agree to the privacy policy to submit." },
                      {}
                    )
                  ),

                  /* ── Submit button ── */
                  a!buttonLayout(
                    primaryButtons: {
                      a!buttonWidget(
                        label: "Send Message",
                        style: "SOLID",
                        width: "FILL",
                        saveInto: local!isSubmitted,
                        value: true,
                        validate: true
                      )
                    }
                  ),

                  /* ── Footer ── */
                  a!richTextDisplayField(
                    labelPosition: "COLLAPSED",
                    value: "We typically respond within 1 business day.",
                    align: "CENTER",
                    marginBelow: "NONE"
                  )
                }
              )
            },
            spacing: "NONE"
          )
        },
        style: "NONE",
        backgroundColor: "#1B3A4B",
        padding: "NONE",
        marginBelow: "NONE",
        showBorder: false
      )
    },
    backgroundColor: "#1B3A4B"
  )
)
