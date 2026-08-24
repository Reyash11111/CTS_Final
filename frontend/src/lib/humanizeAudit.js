// Turns a raw AuditEvent (action + detail JSON) into a short, plain-English
// summary instead of a raw JSON dump. Falls back to a readable "key: value"
// line -- never JSON.stringify -- for any action type not explicitly
// handled below, so a new event type degrades gracefully instead of
// silently going back to being unreadable.

const pct = (v, digits = 0) =>
  v === null || v === undefined ? '—' : `${(v * 100).toFixed(digits)}%`

const short = (id) => (id ? String(id).slice(0, 8) : 'someone')

const HANDLERS = {
  REQUEST_SUBMITTED: (d) =>
    `Case ${d.case_number || ''} submitted — ${d.diagnosis || 'diagnosis not specified'}, requesting ${d.treatment || d.requested_treatment || 'treatment not specified'}.`,

  DOCUMENT_UPLOADED: (d) =>
    `Uploaded "${d.filename}"${d.pages ? ` (${d.pages} pages)` : ''}` +
    (d.confidence != null ? `, ${pct(d.confidence)} of fields extracted.` : '.'),

  VALIDATION_AGENT_COMPLETED: (d) => {
    const bits = []
    bits.push(
      d.contextually_complete
        ? 'Documentation was found complete.'
        : 'Documentation was flagged as incomplete.',
    )
    if (d.missing_context?.length) bits.push(`Missing: ${d.missing_context.join('; ')}.`)
    if (d.documentation_needed?.length) bits.push(`Needs: ${d.documentation_needed.join('; ')}.`)
    if (d.inconsistencies?.length) bits.push(`Inconsistencies found: ${d.inconsistencies.join('; ')}.`)
    if (d.human_review_required) bits.push('Flagged for human review.')
    if (d.confidence != null) bits.push(`Agent confidence ${pct(d.confidence)}.`)
    return bits.join(' ')
  },

  DECISION_COMPUTED: (d) => {
    const outcome = d.decision || (d.status || '').replace(/_/g, ' ') || 'a decision'
    let s = `Engine computed ${outcome}`
    const parts = []
    if (d.necessity_score != null) parts.push(`necessity ${pct(d.necessity_score)}`)
    if (d.policy_fit_score != null) parts.push(`policy fit ${d.policy_fit_score.toFixed(3)}`)
    if (parts.length) s += ` (${parts.join(', ')})`
    if (d.processing_ms != null) s += ` in ${Math.round(d.processing_ms)} ms`
    s += '.'
    if (d.rationale) s += ` ${d.rationale}`
    return s
  },

  HUMAN_REVIEW_QUEUED: (d) => {
    let s = 'Routed to human review'
    if (d.priority) s += ` at ${String(d.priority).toLowerCase()} priority`
    s += '.'
    if (d.assignment_reason) s += ` ${d.assignment_reason}`
    return s
  },

  REVIEWER_ASSIGNED: (d) => d.reason || `Assigned to reviewer ${short(d.reviewer_id)}.`,

  REVIEWER_REASSIGNED: (d) =>
    `Reassigned from ${short(d.from)} to ${short(d.to)}` +
    (d.manual ? ' (manual reassignment).' : ' (automatic reassignment).'),

  REVIEWER_DECISION: (d) => {
    let s = `Reviewer decided ${d.decision || ''}.`
    if (d.agreed_with_engine === false) s += " This overrides the engine's own leaning."
    if (d.notes) s += ` "${d.notes}"`
    return s
  },

  APPEAL_FILED: (d) =>
    `Appeal filed${d.new_documentation ? ' with new documentation' : ''}.` +
    (d.model_predicted ? ` Model-predicted outcome at filing: ${d.model_predicted}.` : ''),

  APPEAL_RESOLVED: (d) =>
    `Appeal ${String(d.outcome || '').toLowerCase()}.` + (d.notes ? ` "${d.notes}"` : ''),

  USER_LOGIN: (d) => `Signed in${d.portal ? ` to the ${d.portal} portal` : ''}.`,

  USER_REGISTERED: (d) =>
    `Account created${d.portal ? ` (${d.portal} portal)` : ''}` +
    (d.organization ? ` for ${d.organization}.` : '.'),

  REVIEWER_AVAILABILITY_CHANGED: (d) =>
    d.is_available ? 'Marked as available for new cases.' : `Paused — ${d.reason || 'unavailable'}.`,
}

export function humanizeAuditEvent(event) {
  const handler = HANDLERS[event.action]
  if (handler) {
    try {
      const text = handler(event.detail || {})
      if (text) return text
    } catch {
      // fields didn't match what the handler expected -- fall through
      // rather than crash the whole audit panel over one bad entry
    }
  }
  return genericSummary(event.detail)
}

// Fallback for anything not explicitly handled above: readable
// "key: value" lines, never a raw JSON dump.
function genericSummary(detail) {
  if (!detail || typeof detail !== 'object' || Object.keys(detail).length === 0) {
    return null
  }
  return Object.entries(detail)
    .filter(([, v]) => v !== null && v !== undefined && v !== '')
    .map(([k, v]) => {
      const label = k.replace(/_/g, ' ')
      const value = Array.isArray(v)
        ? v.join(', ')
        : typeof v === 'object'
          ? Object.entries(v).map(([k2, v2]) => `${k2.replace(/_/g, ' ')}: ${v2}`).join(', ')
          : String(v)
      return `${label}: ${value}`
    })
    .join(' · ')
}