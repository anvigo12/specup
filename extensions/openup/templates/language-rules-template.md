# Language Rules — Simplified Technical English

> **Binding.** This file is part of the agent operating contract (specup.md s7). An agent
> writing any governed document in this repository obeys these rules, the same way it obeys
> "Resolve, or stop — never infer". A human reviewer enforces them; no validator does. Seeded
> from the `openup` extension — amending it is a governance decision, not an edit.

The controlled language is **ASD-STE100, Simplified Technical English**. It exists because technical English has too many ways to say one thing, and a reader must follow its meaning clearly and consistently.
Refer: https://github.com/AminBlg/SimpleEnglish

## Why a governed project needs it

Traceability rests on agreement about what a requirement says. `REQ-AUTH-0014` reaches an implementation, a test and a gate; if two people read the sentence differently, the edges still resolve and the graph still looks green while the three artifacts answer three different questions. Nothing downstream can detect that. Controlled language is the only place it can be prevented.

The same argument holds for the agent. An LLM asked to implement an ambiguous requirement will not stop — it will choose a reading and proceed, which is the s51 failure this whole model exists to prevent.

## Scope

These rules apply to every document an agent writes or edits:

- requirements, acceptance criteria, user stories and business objectives
- `vision.md`, `stakeholders.md`, ADRs, risk titles and mitigation text
- `AGENTS.md`, `index.md` and `skills/*/SKILL.md`
- `description`, `title`, `name` and `terminal_reason` fields in the canonical YAML stores
- RFC 9457 `title` strings (see `coding-rules.md`)
- the text of a report an agent gives a human

They do not apply to: code identifiers, quoted text from an external standard, proper nouns,
file paths, generated views, or this repository's own explanatory prose about its design.

## The rules

### Vocabulary

1. **One word, one meaning. One meaning, one word.** Choose the term once and repeat it.
   Never reach for a synonym to avoid repetition — in technical writing, repetition is
   precision and variation is a new claim.
2. **Use the approved word.** The table below lists the non-approved words seen most often in
   governed documents, each with its replacement.
3. **Keep the project's own vocabulary exact.** `implements`, `verifies`, `refines`,
   `derived`, `asserted`, `approved`, `BASELINED` and the rest of the relation and state
   vocabulary mean exactly what `ID-GRAMMAR.md` says they mean. Never use one loosely in
   prose.
4. **No jargon, no idiom, no slang.** "Wire it up", "out of the box" and "low-hanging fruit"
   have no fixed meaning.
5. **Write out an abbreviation the first time** it appears in a document, then use it
   consistently.

### Sentences

6. **A procedural sentence holds at most 20 words. A descriptive sentence holds at most 25.**
   A sentence that will not fit is usually two sentences.
7. **One instruction per sentence.** Two instructions joined by "and" become two steps.
8. **Use the imperative for an instruction.** Write "Record the evidence", not "The evidence
   should be recorded" and not "You will need to record the evidence".
9. **Use the active voice in a procedure.** The passive hides who acts, and in a governed
   repository the actor is the point.
10. **Use simple tenses** — past, present, future. Avoid the perfect and continuous forms.
11. **Do not drop articles.** "Update the register", not "Update register".
12. **Avoid noun clusters longer than three words.** "Requirement traceability coverage
    threshold report" is a puzzle; "the report on coverage against the traceability threshold"
    is a sentence.
13. **Use a comma before the final "and" or "or"** in a list of three or more items.

### Paragraphs and structure

14. **A descriptive paragraph holds at most six sentences** and covers one topic.
15. **Use a vertical list** when a sentence carries more than two conditions.
16. **Put a warning or a caution before the step it applies to**, never after.
17. **Say what to do, not what not to do**, unless the prohibition is the rule itself.

### Requirements specifically

18. **One requirement per statement**, and it must be testable. If you cannot name the
    observation that would falsify it, it is not a requirement.
19. **Never write "and/or"**. Name which one, or name both.
20. **Never write "etc."** The items it hides are the ones a reader needed.
21. **Use "must" for an obligation and "can" for a possibility.** Do not use "should" in a
    requirement — a reviewer cannot tell whether it binds.

## Non-approved words

Partial by necessity: the ASD-STE100 approved dictionary is a licensed document that SpecUP
cannot redistribute. This table carries the entries that appear most often in governed
documents. Its absence from this table does not make a word approved.

| Do not write | Write |
|---|---|
| accomplish | do |
| additional | more |
| and/or | name which one, or name both |
| approximately | about |
| ascertain | find out |
| assist | help |
| attempt | try |
| commence | start |
| demonstrate | show |
| e.g. | for example |
| endeavour, endeavor | try |
| etc. | name every item |
| facilitate | help |
| i.e. | that is |
| in order to | to |
| initiate | start |
| numerous | many |
| obtain | get |
| prior to | before |
| subsequent to | after |
| sufficient | enough |
| terminate | stop |
| utilise, utilize | use |
| via | by, or through |
| whilst | while |

## Worked examples

| Before | After | Rule |
|---|---|---|
| The certificate should be validated prior to the session being established, and the result logged. | Validate the certificate. Establish the session. Record the result. | 6, 7, 8, 9 |
| It is recommended that the user utilise the approved endpoint. | Use the approved endpoint. | 2, 8 |
| The system shall support authentication and/or authorization as appropriate. | The system must authenticate every request. The system must authorize every request against the target resource. | 18, 19 |
| Numerous validation errors, e.g. malformed input, expired tokens, etc., return 400. | A malformed request body returns 400. An expired token returns 401. | 2, 20 |
| Ensure that the traceability graph has been updated subsequent to implementation. | After you implement the change, update the traceability graph. | 2, 10 |

## What this file does not do

No validator checks these rules. SpecUP's gates check structure and evidence, not prose, so
conformance is established at review — by the human who approves the artifact, using this
file as the standard. An agent that writes a governed document and then reports that it
followed these rules has made a claim, not produced evidence. Treat it as `asserted`.
