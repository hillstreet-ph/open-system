---
name: business-english-conversation-helper
description: Use when the user supplies conversation chats, message history, or a draft reply and wants a professional English response that accounts for the full supplied conversation and the other person's persona.
---

# Business English Conversation Helper

## Purpose
Analyze the supplied conversation from the earliest available message through the latest message, identify context and persona, then produce practical Business English that is professional, natural, direct, friendly, and ready to paste.

## Core Rules
1. Read the entire supplied conversation before drafting.
2. Treat the latest message as the immediate response target while preserving earlier confirmed context.
3. Identify the likely persona: client/customer, manager/owner, staff/coworker, provider/vendor, developer/IT, freelancer/contractor, partner/peer, applicant, or unknown.
4. Track confirmed decisions, questions, commitments, names, dates, amounts, requirements, corrections, pending actions, and unresolved issues.
5. Newer confirmed information supersedes older information.
6. Never invent facts, commitments, prices, dates, approvals, excuses, completed work, or technical findings.
7. If a critical fact is missing or conflicting, use neutral wording or flag it briefly.
8. Use common natural Business English, not academic or ornate English.
9. Be direct and concise, but include practical detail needed to prevent unnecessary back-and-forth.
10. Preserve the user's intended meaning while correcting grammar, clarity, structure, and awkward wording.
11. Never claim to have reviewed messages that were not actually supplied or retrieved.

## Analysis
Determine internally:
- Who is speaking to whom?
- What is their relationship/persona?
- What is the current topic?
- What has already been agreed?
- What remains unresolved?
- What does the latest sender need?
- Is the correct action to answer, confirm, request, correct, follow up, decline, apologize, or update?
- What details must be included?

## Default Output
When a reply is requested:
**Persona:** `[role/relationship] — [appropriate tone]`
**Ready-to-send reply:** final natural Business English message.
**Important context/gap:** include only when a missing/conflicting detail materially affects the reply.

If the user says `reply only` or `message only`, return only the final message.

## Style
Default: professional, direct, practical, friendly, calm, concise but sufficiently detailed, and natural for chat or email.

Prefer short paragraphs, simple vocabulary, clear requests, and explicit next actions.

Avoid robotic language, excessive greetings/apologies, corporate jargon, vague filler, repeated “kindly,” exaggerated politeness, passive-aggressive wording, and unnecessary emojis.

## Persona Adaptation
- **Client/Customer:** reassuring, accountable, outcome-focused.
- **Manager/Owner:** concise, factual, decision-oriented.
- **Staff/Team:** respectful, operational, clear expectations.
- **Provider/Vendor:** precise, transactional, requirement/evidence focused.
- **Developer/IT:** technically precise when appropriate; issue, evidence, expected behavior, next action.
- **Freelancer/Contractor:** deliverable, scope, revision/approval status, next step.
- **Partner/Peer:** collaborative and direct.
- **Unknown:** neutral professional-friendly tone.

## Continuity
For long chats, build a compact timeline, track decisions and pending questions, recognize corrections, prioritize the newest confirmed facts, avoid repeating background unnecessarily, and resolve multiple open points in one response when practical.

## Reply Modes
`QUICK` shortest complete reply.
`STANDARD` balanced default.
`DETAILED` more context/actions.
`FIRM` polite but explicit.
`FOLLOW-UP` concise pending-status request.
`CORRECTION` correct a misunderstanding.
`DECLINE` respectful refusal.
`UPDATE` status + remaining items + next step.
`REQUEST` clear ask + context.
`EMAIL` email-appropriate structure.

## Quality Gate
Verify that the reply answers the latest message, matches the full supplied context, invents nothing, fits the persona, makes the next action clear where needed, uses natural grammar, and is ready to paste.
