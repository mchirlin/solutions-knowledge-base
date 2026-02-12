# Design Document: Complete Evaluation Form - Right Panel with Tabs

## Overview

This document outlines the design for adding a right-hand panel with "Highlights" and "Documents" tabs to the Complete Evaluation form (`AS_GSS_FM_completeEvaluation`).

---

## User Story

As an evaluator, I want to see a right-hand section with "Highlights" and "Documents" tabs when completing an evaluation, so I can quickly access relevant information and documents while working.

### Acceptance Criteria

| AC | Given | When | Then |
|----|-------|------|------|
| AC1 | I am an evaluator and I open the Complete Evaluation form | The form is displayed | A right-hand section should be visible with tabs labeled "Highlights" and "Documents" |
| AC2 | The right-hand section with tabs is displayed | I click on the "Documents" tab | The relevant documents for the evaluation should be displayed |
| AC3 | The Documents tab is selected | The documents are rendered | They should be displayed using the new design as per the provided mockups |

---

## Current State Analysis

### Existing Form Structure

The Complete Evaluation form (`AS_GSS_FM_completeEvaluation`) currently includes:

**Main Interface Components:**
- `AS_GSS_CPS_completeEvaluationHeader` — Header section
- `AS_GSS_CPS_evaluationResponses` — Evaluation responses section
- `AS_GSS_CPS_finalRatingsForCompleteEvaluation` — Final ratings section
- `AS_GSS_CPS_ratingJustification` — Rating justification section
- `AS_GSS_CPS_evalDocsForCompleteEvaluation` — Document upload section (current implementation)
- `AS_GSS_SCT_evaluationTaskDocumentDisplay` — Document display section

**Data Dependencies:**
- `AS_GSS_QE_getEvaluationDocuments` — Fetches evaluation documents
- `AS_GSS_QE_getEvaluationFactorDocumentMapping` — Gets factor-document mappings
- `AS_GSS_QE_getEvaluationCriteria` — Retrieves evaluation criteria
- `AS_GSS_QE_getEvaluationResponses` — Gets evaluation responses

### Existing Tab/Panel Patterns in Application

The application has an established pattern for right panels with tabs in the Consensus Form:

**Reference Implementation:** `AS_GSS_CPS_consensusFormRighPanel`
- Contains multiple tab sections
- Calls child interfaces for each tab content:
  - `AS_GSS_CPS_consensusFormRightPanel_Factordetails`
  - `AS_GSS_CPS_consensusFormRightPanel_EvaluatorRatings`
  - `AS_GSS_CPS_consensusFormRightPanel_FactorDocuments`

**Tab Implementation Pattern:** `AS_GSS_consensusReportSummaryTabs`
- Uses `a!localVariables` for tab state management
- Leverages branding constants via `AS_GSS_BrandingValueByKey`
- Supports automation testing via `AS_GSS_TOGGLE_AUTOMATION_TESTING_ENABLED`

### Existing Document Display Components

| Component | Purpose | Reusability |
|-----------|---------|-------------|
| `AS_GSS_SCT_evaluationDocumentsList` | Lists evaluation documents | High - can be reused |
| `AS_GSS_CRD_displayEvaluationDocument` | Individual document card | High - can be reused |
| `AS_GSS_CO_documentDownloadLink` | Document download link | High - can be reused |
| `AS_GSS_CPS_documentViewer` | Document viewer/preview | Medium - may need adaptation |
| `AS_GSS_UT_displayDocumentName` | Document name formatting | High - utility rule |
| `AS_GSS_UT_displayDocumentSize` | Document size formatting | High - utility rule |

---

## Proposed Design

### Mockup Analysis

Based on the provided mockup, the right panel has the following characteristics:

**Tab Bar Design:**
- 4 tabs: "ALL FINDINGS" | "STRENGTHS" | "RISK" | "DOCUMENTS"
- "ALL FINDINGS" is the default/first tab (highlighted with underline)
- Tabs are displayed in a horizontal row with equal spacing
- Active tab has a visual indicator (underline/highlight)

**Findings Content Structure (ALL FINDINGS tab):**
Each finding is displayed as a card with:
- **Finding Title** (e.g., "DEPLOYMENT", "SCALABILITY", "ARCHITECTURE") — Bold, uppercase
- **Description** — Multi-line text describing the finding
- **Reference Link** — Purple/blue link text (e.g., "Volume 2, Section 1, Page 12-14")
- Cards are separated by subtle dividers or spacing

**Purpose:** Display a brief list of all findings for that particular factor for that particular vendor

### Architecture Overview

```
AS_GSS_FM_completeEvaluation (Modified)
├── Left Section (Existing - ~65% width)
│   ├── AS_GSS_CPS_completeEvaluationHeader
│   ├── AS_GSS_CPS_evaluationResponses
│   ├── AS_GSS_CPS_finalRatingsForCompleteEvaluation
│   └── AS_GSS_CPS_ratingJustification
│
└── Right Section (NEW - ~35% width)
    └── AS_GSS_CPS_completeEvaluationRightPanel (NEW)
        ├── Tab Navigation Bar
        │   ├── "ALL FINDINGS" tab (default)
        │   ├── "STRENGTHS" tab
        │   ├── "RISK" tab
        │   └── "DOCUMENTS" tab
        │
        ├── AS_GSS_CPS_completeEvalAllFindingsTab (NEW)
        │   └── AS_GSS_CRD_findingCard (NEW) - repeated for each finding
        │
        ├── AS_GSS_CPS_completeEvalStrengthsTab (NEW)
        │   └── Filtered findings (strengths only)
        │
        ├── AS_GSS_CPS_completeEvalRiskTab (NEW)
        │   └── Filtered findings (risks/weaknesses/deficiencies)
        │
        └── AS_GSS_CPS_completeEvalDocumentsTab (NEW)
            └── AS_GSS_SCT_evaluationDocumentsList (Reused/Modified)
```

### New Objects to Create

#### 1. AS_GSS_CPS_completeEvaluationRightPanel (Interface)

**Purpose:** Container for the right panel with 4-tab navigation displaying findings and documents

**Inputs:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `evaluationId` | Integer | The evaluation record ID |
| `vendorId` | Integer | The vendor being evaluated |
| `criteriaId` | Integer | Current criteria/factor ID |
| `evaluationResponses` | CDT Array | All evaluation responses for the factor/vendor |
| `i18nData` | Map | Internationalization bundle |

**Local Variables:**
| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `local!selectedTab` | Integer | 1 | Active tab (1=All Findings, 2=Strengths, 3=Risk, 4=Documents) |
| `local!allFindings` | CDT Array | - | All responses/findings for current factor |
| `local!strengths` | CDT Array | - | Filtered strengths only |
| `local!risks` | CDT Array | - | Filtered weaknesses/deficiencies |

**SAIL Structure:**
```sail
a!localVariables(
  local!selectedTab: 1,
  
  /* Filter findings by response type */
  local!allFindings: ri!evaluationResponses,
  local!strengths: rule!AS_CO_UT_filterCdtByField(
    cdt: ri!evaluationResponses,
    field: "responseTypeId",
    value: cons!AS_GSS_REF_ID_RESPONSE_TYPE_STRENGTH
  ),
  local!risks: rule!AS_CO_UT_filterCdtByMultipleFieldValuePairs(
    cdt: ri!evaluationResponses,
    fieldValuePairs: {
      { field: "responseTypeId", values: {
        cons!AS_GSS_REF_ID_RESPONSE_TYPE_WEAKNESS,
        cons!AS_GSS_REF_ID_RESPONSE_TYPE_DEFICIENCY
      }}
    }
  ),
  
  local!tabConfig: {
    { label: "ALL FINDINGS", index: 1 },
    { label: "STRENGTHS", index: 2 },
    { label: "RISK", index: 3 },
    { label: "DOCUMENTS", index: 4 }
  },
  
  a!sectionLayout(
    contents: {
      /* Tab Navigation Bar */
      a!columnsLayout(
        columns: a!forEach(
          items: local!tabConfig,
          expression: a!columnLayout(
            width: "AUTO",
            contents: a!richTextDisplayField(
              value: a!richTextItem(
                text: fv!item.label,
                link: a!dynamicLink(
                  value: fv!item.index,
                  saveInto: local!selectedTab
                ),
                style: if(
                  local!selectedTab = fv!item.index,
                  "STRONG",
                  "PLAIN"
                ),
                color: if(
                  local!selectedTab = fv!item.index,
                  "ACCENT",
                  "SECONDARY"
                )
              )
            )
          )
        ),
        spacing: "DENSE"
      ),
      
      /* Active Tab Indicator Line */
      a!richTextDisplayField(
        value: a!richTextItem(
          text: repeat(50, "─"),
          color: "SECONDARY"
        )
      ),
      
      /* Tab Content - All Findings */
      a!showWhen(
        showWhen: local!selectedTab = 1,
        contents: rule!AS_GSS_CPS_completeEvalAllFindingsTab(
          findings: local!allFindings,
          i18nData: ri!i18nData
        )
      ),
      
      /* Tab Content - Strengths */
      a!showWhen(
        showWhen: local!selectedTab = 2,
        contents: rule!AS_GSS_CPS_completeEvalStrengthsTab(
          findings: local!strengths,
          i18nData: ri!i18nData
        )
      ),
      
      /* Tab Content - Risk */
      a!showWhen(
        showWhen: local!selectedTab = 3,
        contents: rule!AS_GSS_CPS_completeEvalRiskTab(
          findings: local!risks,
          i18nData: ri!i18nData
        )
      ),
      
      /* Tab Content - Documents */
      a!showWhen(
        showWhen: local!selectedTab = 4,
        contents: rule!AS_GSS_CPS_completeEvalDocumentsTab(
          evaluationId: ri!evaluationId,
          vendorId: ri!vendorId,
          criteriaId: ri!criteriaId,
          i18nData: ri!i18nData
        )
      )
    }
  )
)
```

#### 2. AS_GSS_CPS_completeEvalAllFindingsTab (Interface)

**Purpose:** Display all findings (strengths, weaknesses, deficiencies) for the current factor/vendor

**Inputs:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `findings` | CDT Array | All evaluation response findings |
| `i18nData` | Map | Internationalization bundle |

**SAIL Structure:**
```sail
a!localVariables(
  a!forEach(
    items: ri!findings,
    expression: rule!AS_GSS_CRD_findingCard(
      finding: fv!item,
      i18nData: ri!i18nData
    )
  )
)
```

#### 3. AS_GSS_CPS_completeEvalStrengthsTab (Interface)

**Purpose:** Display only strength findings

**Inputs:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `findings` | CDT Array | Filtered strength findings |
| `i18nData` | Map | Internationalization bundle |

**Implementation:** Same structure as All Findings tab, receives pre-filtered data

#### 4. AS_GSS_CPS_completeEvalRiskTab (Interface)

**Purpose:** Display risk findings (weaknesses and deficiencies)

**Inputs:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `findings` | CDT Array | Filtered weakness/deficiency findings |
| `i18nData` | Map | Internationalization bundle |

**Implementation:** Same structure as All Findings tab, receives pre-filtered data

#### 5. AS_GSS_CRD_findingCard (Interface) — KEY NEW COMPONENT

**Purpose:** Display a single finding card per the mockup design

**Inputs:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `finding` | CDT | Single evaluation response/finding record |
| `i18nData` | Map | Internationalization bundle |

**Visual Design (per mockup):**
```
┌─────────────────────────────────────────────┐
│ DEPLOYMENT                                   │  ← Title (bold, uppercase)
│                                             │
│ Comprehensive cloud-native solution on      │  ← Description text
│ FedRAMP High authorized infrastructure -    │     (multi-line, normal weight)
│ FedRAMP High standards required.            │
│ Moderate baseline per differentiated        │
│ criteria.                                   │
│                                             │
│ 📄 Volume 2, Section 1, Page 12-14          │  ← Reference link (purple/accent)
└─────────────────────────────────────────────┘
```

**SAIL Structure:**
```sail
a!cardLayout(
  contents: {
    a!richTextDisplayField(
      value: a!richTextItem(
        text: upper(ri!finding.title),
        style: "STRONG",
        size: "MEDIUM"
      )
    ),
    a!richTextDisplayField(
      value: ri!finding.description,
      marginBelow: "STANDARD"
    ),
    a!richTextDisplayField(
      value: a!richTextItem(
        text: ri!finding.reference,
        link: a!dynamicLink(
          value: ri!finding.referenceLink,
          saveInto: {}
        ),
        linkStyle: "STANDALONE",
        color: "ACCENT"
      )
    )
  },
  style: "NONE",
  marginBelow: "STANDARD",
  padding: "STANDARD"
)
```

**Data Mapping:**
| Mockup Element | Field Source | Notes |
|----------------|--------------|-------|
| Title | `finding.title` or derived from response type | e.g., "DEPLOYMENT", "SCALABILITY" |
| Description | `finding.description` or `finding.justification` | The finding narrative |
| Reference | `finding.reference` | e.g., "Volume 2, Section 1, Page 12-14" |

#### 6. AS_GSS_CPS_completeEvalDocumentsTab (Interface)

**Purpose:** Display documents related to the evaluation

**Inputs:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `evaluationId` | Integer | The evaluation record ID |
| `vendorId` | Integer | The vendor being evaluated |
| `criteriaId` | Integer | Current criteria/factor ID (for filtering) |
| `i18nData` | Map | Internationalization bundle |

**Data Queries:**
```sail
local!documents: rule!AS_GSS_QE_getEvaluationDocuments(
  evaluationId: ri!evaluationId,
  returnType: cons!AS_CO_ENUM_QE_RETURN_TYPE_OBJECT_ARRAY
)

/* Filter to relevant documents for current factor/vendor */
local!relevantDocuments: rule!AS_CO_UT_filterCdtByMultipleFieldValuePairs(
  cdt: local!documents,
  fieldValuePairs: {
    { field: "vendorId", value: ri!vendorId },
    { field: "criteriaId", value: ri!criteriaId }
  }
)
```

**Document Categories to Display:**
| Category | Constant | Description |
|----------|----------|-------------|
| Factor Documents | `AS_GSS_REF_ID_DOC_TYPE_FACTOR` | Documents related to evaluation factors |
| Reference Documents | `AS_GSS_REF_ID_DOC_TYPE_REFERENCE` | Reference materials |
| Vendor Documents | `AS_GSS_REF_ID_DOC_TYPE_VENDOR` | Vendor-submitted documents |

---

## Objects to Modify

### AS_GSS_FM_completeEvaluation

**Changes Required:**

1. **Layout Restructure:** Convert from single-column to two-column layout
   ```sail
   a!columnsLayout(
     columns: {
       a!columnLayout(
         width: "WIDE",  /* ~70% */
         contents: { /* Existing form content */ }
       ),
       a!columnLayout(
         width: "NARROW",  /* ~30% */
         contents: rule!AS_GSS_CPS_completeEvaluationRightPanel(...)
       )
     }
   )
   ```

2. **Pass Required Data:** Ensure evaluation context is passed to right panel

3. **Remove Redundant Document Section:** If documents move entirely to right panel, remove `AS_GSS_CPS_evalDocsForCompleteEvaluation` from main form (or keep for upload functionality)

---

## Translation Keys Required

Add to internationalization bundle:

| Key | English Value | Description |
|-----|---------------|-------------|
| `lbl_AllFindings` | ALL FINDINGS | Tab label |
| `lbl_Strengths` | STRENGTHS | Tab label |
| `lbl_Risk` | RISK | Tab label |
| `lbl_Documents` | DOCUMENTS | Tab label |
| `lbl_NoFindingsAvailable` | No findings available | Empty state for findings tabs |
| `lbl_NoDocumentsAvailable` | No documents available | Empty state for documents tab |
| `lbl_NoStrengthsAvailable` | No strengths available | Empty state for strengths tab |
| `lbl_NoRisksAvailable` | No risks available | Empty state for risk tab |

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    AS_GSS_FM_completeEvaluation                  │
│                                                                  │
│  ┌─────────────────────┐    ┌─────────────────────────────────┐ │
│  │   Process Model     │    │         Interface               │ │
│  │   Parameters        │───▶│                                 │ │
│  │   - evaluationId    │    │  ┌───────────┐  ┌────────────┐  │ │
│  │   - vendorId        │    │  │ Left Col  │  │ Right Col  │  │ │
│  │   - taskId          │    │  │ (~65%)    │  │ (~35%)     │  │ │
│  │   - criteriaId      │    │  │           │  │            │  │ │
│  │   - responses       │    │  │ (Existing │  │ (NEW)      │  │ │
│  └─────────────────────┘    │  │  Content) │  │ Right      │  │ │
│                             │  │           │  │ Panel      │  │ │
│                             │  └───────────┘  └─────┬──────┘  │ │
│                             └───────────────────────┼─────────┘ │
└─────────────────────────────────────────────────────┼───────────┘
                                                      │
                                                      ▼
                    ┌──────────────────────────────────────────────┐
                    │  AS_GSS_CPS_completeEvaluationRightPanel      │
                    │                                              │
                    │  ┌────────────────────────────────────────┐  │
                    │  │ [ALL FINDINGS] [STRENGTHS] [RISK] [DOCS]│  │
                    │  └────────────────────────────────────────┘  │
                    │                                              │
                    │  local!selectedTab                           │
                    │       │                                      │
                    │       ├──▶ Tab 1: All Findings               │
                    │       │    └─▶ AS_GSS_CPS_completeEvalAllFindingsTab │
                    │       │         └─▶ AS_GSS_CRD_findingCard (×N) │
                    │       │                                      │
                    │       ├──▶ Tab 2: Strengths                  │
                    │       │    └─▶ AS_GSS_CPS_completeEvalStrengthsTab │
                    │       │         └─▶ Filtered by STRENGTH type│
                    │       │                                      │
                    │       ├──▶ Tab 3: Risk                       │
                    │       │    └─▶ AS_GSS_CPS_completeEvalRiskTab │
                    │       │         └─▶ Filtered by WEAKNESS/DEFICIENCY │
                    │       │                                      │
                    │       └──▶ Tab 4: Documents                  │
                    │            └─▶ AS_GSS_CPS_completeEvalDocumentsTab │
                    │                 └─▶ AS_GSS_QE_getEvaluationDocuments │
                    └──────────────────────────────────────────────┘
```

### Finding Card Data Mapping

```
┌─────────────────────────────────────────────────────────────────┐
│  AS_GSS_EvaluationResponses_SYNCEDRECORD                        │
│                                                                  │
│  ┌─────────────────┐     ┌─────────────────────────────────────┐│
│  │ responseTypeId  │────▶│ Determines category (Strength/Risk) ││
│  │ title           │────▶│ Finding Title (uppercase display)   ││
│  │ description     │────▶│ Finding Description text            ││
│  │ justification   │────▶│ Alternative description source      ││
│  │ reference       │────▶│ "Volume 2, Section 1, Page 12-14"   ││
│  │ referenceLink   │────▶│ Link destination for reference      ││
│  │ criteriaId      │────▶│ Links to factor/criteria            ││
│  │ vendorId        │────▶│ Links to vendor being evaluated     ││
│  └─────────────────┘     └─────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Steps

### Phase 1: Create Finding Card Component

1. Create `AS_GSS_CRD_findingCard`
   - Implement card layout per mockup
   - Title in bold uppercase
   - Description text
   - Reference link with accent color
   - Handle empty/null fields gracefully

### Phase 2: Create Tab Content Interfaces

2. Create `AS_GSS_CPS_completeEvalAllFindingsTab`
   - Loop through all findings
   - Render finding cards
   - Handle empty state

3. Create `AS_GSS_CPS_completeEvalStrengthsTab`
   - Display pre-filtered strength findings
   - Same card rendering pattern

4. Create `AS_GSS_CPS_completeEvalRiskTab`
   - Display pre-filtered weakness/deficiency findings
   - Same card rendering pattern

5. Create `AS_GSS_CPS_completeEvalDocumentsTab`
   - Query evaluation documents
   - Display using existing document components
   - Filter by current factor/vendor context

### Phase 3: Create Right Panel Container

6. Create `AS_GSS_CPS_completeEvaluationRightPanel`
   - Implement 4-tab navigation bar
   - Tab state management
   - Filter findings by response type
   - Conditional rendering of tab content

### Phase 4: Modify Existing Form

7. Modify `AS_GSS_FM_completeEvaluation`
   - Restructure to two-column layout (~65%/~35%)
   - Integrate right panel
   - Pass evaluation responses and context to right panel

### Phase 5: Testing & Refinement

8. Add translation keys to bundle
9. Test tab switching behavior
10. Verify findings display correctly per response type
11. Test with various evaluation states (no findings, many findings)
12. Ensure responsive behavior

---

## Reusable Components

### From Existing Codebase

| Component | Usage |
|-----------|-------|
| `AS_GSS_BrandingValueByKey` | Tab styling, colors |
| `AS_GSS_CO_UT_loadBundleFromFolder` | i18n loading |
| `AS_CO_I18N_UT_displayLabel` | Label display |
| `AS_GSS_QE_getEvaluationDocuments` | Document query |
| `AS_GSS_QE_getEvaluationResponses` | Evaluation responses query |
| `AS_CO_UT_filterCdtByField` | Filtering by response type |
| `AS_CO_UT_filterCdtByMultipleFieldValuePairs` | Multi-value filtering |
| `AS_GSS_UT_displayDocumentName` | Document name formatting |
| `AS_GSS_UT_displayDocumentSize` | File size formatting |
| `AS_GSS_CO_documentDownloadLink` | Download link component |
| `AS_GSS_CP_singleClickDocumentDownloadLinkFromExternalSource` | External doc downloads |

### Pattern References

| Pattern | Reference Object |
|---------|------------------|
| Right Panel with Tabs | `AS_GSS_CPS_consensusFormRighPanel` |
| Tab Navigation | `AS_GSS_consensusReportSummaryTabs` |
| Document List | `AS_GSS_SCT_evaluationDocumentsList` |
| Document Card | `AS_GSS_CRD_displayEvaluationDocument` |
| Response Type Filtering | `AS_GSS_CPS_evaluationResponses` |

### Response Type Constants

| Constant | Purpose |
|----------|---------|
| `AS_GSS_REF_ID_RESPONSE_TYPE_STRENGTH` | Filter for Strengths tab |
| `AS_GSS_REF_ID_RESPONSE_TYPE_WEAKNESS` | Filter for Risk tab |
| `AS_GSS_REF_ID_RESPONSE_TYPE_DEFICIENCY` | Filter for Risk tab |

---

## Testing Considerations

### Functional Tests

- [ ] Tab navigation works correctly (ALL FINDINGS → STRENGTHS → RISK → DOCUMENTS)
- [ ] ALL FINDINGS tab shows all response types
- [ ] STRENGTHS tab shows only strength responses
- [ ] RISK tab shows only weakness and deficiency responses
- [ ] DOCUMENTS tab loads and displays evaluation documents
- [ ] Finding cards display title, description, and reference correctly
- [ ] Reference links are clickable and functional
- [ ] Tab state persists during form interaction

### Edge Cases

- [ ] Evaluation with no findings (empty state for all tabs)
- [ ] Evaluation with only strengths (Risk tab empty)
- [ ] Evaluation with only weaknesses/deficiencies (Strengths tab empty)
- [ ] Evaluation with no documents
- [ ] Large number of findings (scrolling behavior)
- [ ] Findings with missing reference data
- [ ] Long description text (text wrapping)

### Accessibility

- [ ] Tab navigation keyboard accessible (arrow keys, Enter)
- [ ] Screen reader announces active tab
- [ ] Finding cards have proper heading hierarchy
- [ ] Reference links have descriptive labels
- [ ] Color contrast meets WCAG standards

---

## Dependencies

### Process Model
- `AS GSS Complete Evaluation` — Must pass required parameters to interface

### Record Types
- `AS_GSS_EvaluationDocument_SYNCEDRECORD` — Document records
- `AS_GSS_Evaluation_SYNCEDRECORD` — Evaluation records
- `AS_GSS_EvaluationResponses_SYNCEDRECORD` — Evaluation response/findings records

### Constants
- `AS_GSS_REF_ID_DOC_TYPE_FACTOR`
- `AS_GSS_REF_ID_DOC_TYPE_REFERENCE`
- `AS_GSS_REF_ID_DOC_TYPE_VENDOR`
- `AS_GSS_REF_ID_DOC_TYPE_EVALUATOR`
- `AS_GSS_REF_ID_RESPONSE_TYPE_STRENGTH`
- `AS_GSS_REF_ID_RESPONSE_TYPE_WEAKNESS`
- `AS_GSS_REF_ID_RESPONSE_TYPE_DEFICIENCY`

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Form width constraints on smaller screens | Medium | Implement responsive breakpoints, consider collapsible panel |
| Performance with many documents | Low | Implement lazy loading or pagination |
| Breaking existing form functionality | High | Thorough regression testing, feature flag for rollout |
| Inconsistent styling with mockups | Medium | Close collaboration with UX during implementation |

---

## Future Enhancements

1. **Finding Count Badges:** Add count badges to tabs (e.g., "STRENGTHS (3)")
2. **Finding Search/Filter:** Search within findings by keyword
3. **Document Preview:** Inline document preview without download
4. **Contextual Filtering:** Auto-filter findings based on current factor being evaluated
5. **Finding Actions:** Add ability to edit/delete findings from right panel
6. **Collapse/Expand:** Allow collapsing the right panel for more form space
7. **Finding Sorting:** Sort findings by date, type, or relevance

---

## Appendix: Object Naming Conventions

Following existing application patterns:

| Prefix | Type | Example |
|--------|------|---------|
| `AS_GSS_FM_` | Form Interface | `AS_GSS_FM_completeEvaluation` |
| `AS_GSS_CPS_` | Component/Section | `AS_GSS_CPS_completeEvaluationRightPanel` |
| `AS_GSS_CRD_` | Card Component | `AS_GSS_CRD_findingCard` |
| `AS_GSS_SCT_` | Section Component | `AS_GSS_SCT_evaluationDocumentsList` |
| `AS_GSS_QE_` | Query Expression Rule | `AS_GSS_QE_getEvaluationDocuments` |
| `AS_GSS_UT_` | Utility Expression Rule | `AS_GSS_UT_displayDocumentName` |

---

## Appendix: New Objects Summary

| Object Name | Type | Purpose |
|-------------|------|---------|
| `AS_GSS_CPS_completeEvaluationRightPanel` | Interface | Main right panel container with 4-tab navigation |
| `AS_GSS_CPS_completeEvalAllFindingsTab` | Interface | All Findings tab content |
| `AS_GSS_CPS_completeEvalStrengthsTab` | Interface | Strengths tab content (filtered) |
| `AS_GSS_CPS_completeEvalRiskTab` | Interface | Risk tab content (filtered) |
| `AS_GSS_CPS_completeEvalDocumentsTab` | Interface | Documents tab content |
| `AS_GSS_CRD_findingCard` | Interface | Individual finding card component |

---

## Appendix: Mockup Reference

**Tab Bar Layout:**
```
┌──────────────────────────────────────────────────────────────┐
│  [ALL FINDINGS]    [STRENGTHS]    [RISK]    [DOCUMENTS]      │
│  ═══════════════                                             │
└──────────────────────────────────────────────────────────────┘
```

**Finding Card Layout:**
```
┌──────────────────────────────────────────────────────────────┐
│  DEPLOYMENT                                                   │
│                                                              │
│  Comprehensive cloud-native solution on FedRAMP High         │
│  authorized infrastructure - FedRAMP High standards required.│
│  Moderate baseline per differentiated criteria.              │
│                                                              │
│  📄 Volume 2, Section 1, Page 12-14                          │
├──────────────────────────────────────────────────────────────┤
│  SCALABILITY                                                 │
│                                                              │
│  Supports horizontal scaling to 10,000+ concurrent users.    │
│                                                              │
│  📄 Volume 2, Section 1, Page 12-14                          │
├──────────────────────────────────────────────────────────────┤
│  ARCHITECTURE                                                │
│                                                              │
│  Comprehensive cloud-native solution on FedRAMP High         │
│  authorized infrastructure - FedRAMP High standards required.│
│  Moderate baseline per differentiated criteria.              │
│                                                              │
│  📄 Volume 2, Section 1, Page 12-14                          │
└──────────────────────────────────────────────────────────────┘
```
