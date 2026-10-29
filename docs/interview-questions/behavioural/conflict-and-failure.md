# Conflict and Failure Questions

Templates for questions about disagreement, feedback, mistakes, production incidents, and what you changed afterwards. Interviewers want to see ownership, calm judgement, and learning. Use your own experience; where a template describes a situation you have not been in, say so and describe how you would respond.

---

## 1. Tell me about a disagreement with a colleague.

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Choose a real, professional disagreement about an idea, not a person. Show that you understood their position, separated the facts from the preferences, and reached a decision or a clear next step without damaging the relationship.

### Explanation
**Template:**

```text
Situation: [Colleague's role] and I disagreed about [specific technical or process question].
Task:      We needed to [decide / deliver] by [constraint].
Action:    I asked them to walk me through their reasoning, and I restated it to check
           I understood it. I wrote down the facts we both agreed on and the points
           where we differed. I proposed [a test, a prototype, or a measurement] to
           settle the open question. [Outcome of that test or discussion].
Result:    We [decided / shipped] [outcome]. The relationship [stayed strong / improved].
           I learned that [insight about disagreement].
```

**What interviewers listen for:** whether you argued the idea, not the person; whether you were willing to change your mind.

### When to use / pitfalls
- Do not pick a disagreement where you were clearly right and they were clearly wrong. Pick one where both views had merit.
- Do not describe the other person as difficult. Describe the situation and your response.

**See also:** [Leadership and teamwork](leadership-and-teamwork.md)

</details>

---

## 2. Tell me about a time you disagreed with a manager's decision.

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Show that you raised your concern privately, with evidence, at the right time, and that you committed to the decision once it was made, even if you had argued against it. Interviewers look for the difference between disagreeing and undermining.

### Explanation
**Template:**

```text
Situation: My manager proposed [decision] for [reason], and I had concerns about [specific risk].
Task:      I needed to raise the concern without delaying the work unnecessarily.
Action:    I asked for a short one-to-one, explained the risk with [data or an example],
           and proposed [an alternative or a check]. We agreed to [outcome].
Result:    [What happened]. Whether or not I was right, I [committed to / supported]
           the decision, and I learned [insight].
```

### When to use / pitfalls
- Do not raise the concern for the first time in a group meeting.
- If the decision was harmful or unethical, say you escalated it through the proper channel. Choose a story where you did.

**See also:** [Conflict and failure](conflict-and-failure.md)

</details>

---

## 3. Tell me about a time you failed.

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Pick a real failure that was your responsibility and not catastrophic. Describe what went wrong, what you owned, what you did to fix it, and the specific change you made afterwards. The learning must be concrete.

### Explanation
**Template:**

```text
Situation: I was responsible for [area], and I [what you did or did not do].
Task:      The goal was [target], and it was at risk because [consequence].
Action:    I [acknowledged the problem early], [told the people affected], and
           [fixed the immediate issue]. Then I [looked for the root cause], which was
           [cause, such as an unchecked assumption or a missing test].
Result:    [Outcome, including any cost]. I now [specific practice you adopted],
           and I have used it on [later project] to [effect].
```

**Guidance:** name the mistake plainly. "I did not check X before deploying" is stronger than "there was a communication gap".

### When to use / pitfalls
- "My biggest weakness is perfectionism" is not a failure story. Do not use it.
- Do not choose a failure that happened to someone else and present it as yours.

**See also:** [STAR method](star-method.md)

</details>

---

## 4. Tell me about a production incident you were involved in.

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Describe your role in detecting, mitigating, and communicating the incident, and what the blameless review changed. Interviewers want to see calm triage, clear communication, and a fix to the system, not only to the code.

### Explanation
**Template:**

```text
Situation: [Service] started [symptom, such as errors or slow responses] after [change or trigger].
Task:      I was [on call / asked to help] to restore service and find the cause.
Action:    I [checked the dashboards and recent deployments], [rolled back or applied
           a mitigation], and [posted status updates every [interval] to [audience]].
           After service was restored, I [led or joined] a blameless review that found
           [root cause].
Result:    Service was restored in [time]. We changed [system fix, such as a canary
           step, a test, or an alert], and I learned [insight].
```

**Useful structure for a review:** timeline, impact, root cause, contributing factors, what went well, and action items with owners.

### When to use / pitfalls
- Do not name the person who made the change as the cause. Describe the gap in the process.
- If you did not lead the incident, say what you did and do not claim the lead's role.

**See also:** [DevOps, cloud, and AI](../technical/devops-cloud-and-ai-part-1.md)

</details>

---

## 5. How do you give critical feedback to a colleague?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Give feedback privately, soon after the event, focused on a specific behaviour and its effect, and ask for their view. Make it a conversation, and agree on a next step.

### Explanation
**Structure (SBI: Situation, Behaviour, Impact):**

```text
"In [situation], when you [specific behaviour], the effect was [impact on the team, the
work, or the user]. What was your view of it? I would like us to [agreed next step]."
```

**Guidance:**

- Separate the observation from your interpretation: "the deploy was late" rather than "you are careless".
- Listen to the reply. You may have missed context.
- Follow up on the next occasion, and say when you see improvement.

### When to use / pitfalls
- Do not give feedback in public, or through a third party.
- Avoid a "feedback sandwich" that hides the message. Be clear and kind.

**See also:** [Leadership and teamwork](leadership-and-teamwork.md)

</details>

---

## 6. Tell me about a deadline you could not meet.

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Show that you raised the risk early, offered options, communicated the change to stakeholders, and delivered the agreed part on time. Early warning matters more than the miss itself.

### Explanation
**Template:**

```text
Situation: [Deliverable] was due on [date], and [reason, such as a dependency or scope growth].
Task:      I was responsible for [delivery].
Action:    As soon as I saw the risk, I [told the stakeholders], [listed options: reduce scope,
           extend the date, or add people], and [proposed the option we chose]. I [updated the
           plan daily / weekly].
Result:    We delivered [what was delivered] on [date], and [what was deferred] on [date].
           I learned that [insight about estimates or early warning].
```

### When to use / pitfalls
- Do not present a late delivery as on time by redefining "done".
- Say how you improved estimates, or how you now flag risk earlier.

**See also:** [Leadership and teamwork](leadership-and-teamwork.md)

</details>

---

## 7. What is the biggest technical mistake you have made, and what changed?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Name the technical decision, why it looked reasonable at the time, what it cost, and the practice you adopted so the same class of mistake is caught earlier. This question tests self-awareness and engineering judgement.

### Explanation
**Template:**

```text
Mistake:    I [chose / implemented / skipped] [specific technical decision] because
            [reasoning at the time].
Cost:       It caused [effect, such as a data issue, a slow query, or an outage].
Fix:        I [how you fixed it] and [how you verified it].
Change:     I now [practice, such as a load test, a migration rule, or a design review
            checklist].
```

**Examples of practices that fit this template:** writing an idempotency check before a retry was added, running `EXPLAIN` before shipping a new query, or adding a feature flag before a risky change.

### When to use / pitfalls
- Choose a mistake with real consequences, but not one that puts the company at risk in the interview.
- Show the reasoning at the time. Interviewers want to see how you decide, not only how you fix.

**See also:** [Data and persistence](../technical/data-and-persistence-part-1.md)

</details>

---

## 8. How do you handle a difficult stakeholder who keeps changing requirements?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Make the requirements explicit and written, show the cost of each change, and agree on a process for changes such as a change log or a fixed review point. Stay respectful, and keep the focus on the goal the stakeholder cares about.

### Explanation
**Approach:**

1. Ask what outcome the stakeholder needs, not only what they asked for.
2. Write down the current requirements and confirm them in writing.
3. When a change arrives, state its impact on time and scope, and let the stakeholder choose.
4. Agree on a cadence for changes, for example a weekly review, and stick to it.
5. Keep a record, so decisions are not reopened without reason.

**Template:** "I [wrote down / confirmed] the requirements and [showed the impact] of the change. We [agreed to / deferred] it to [date]. Afterwards, the team [delivered / stayed focused] and the stakeholder [result]."

### When to use / pitfalls
- Do not agree to every change silently. Silence becomes an expectation.
- Do not make the stakeholder look foolish in front of others.

**See also:** [Leadership and teamwork](leadership-and-teamwork.md)

</details>

---

## Quick recap

- Pick real disagreements about ideas, and show you understood the other view.
- Disagree before a decision, and commit after it.
- A good failure story has ownership, a fix, and a specific practice that changed.
- Incident answers show calm triage, clear updates, and blameless review.
- Give feedback privately, specifically, and with a next step.

**See also:** [STAR method](star-method.md), [Leadership and teamwork](leadership-and-teamwork.md), [Career motivation](career-motivation.md)
