# Interview Process

This page covers how to prepare for a technical interview, how to handle each round while it happens, and what to do afterwards. The practice questions are elsewhere: coding problems in [Coding questions](coding/index.md), conceptual questions in [Technical questions](technical/index.md), and behavioural stories in [Behavioural questions](behavioural/index.md).

---

## Before the interview

### Research the company

Know enough to ask intelligent questions and to tailor your examples:

- What the business sells or runs, and who its customers are.
- The likely technology stack, from the job description and public engineering material.
- Recent news, such as a product launch, a funding round, or a platform change.
- How the company describes its culture and working style.

You do not need to memorise facts. A few specific details, mentioned naturally, show that you prepared.

### Build a practice plan

Structure practice around the rounds you will face:

1. **Coding**: work through problems by pattern (arrays, graphs, dynamic programming, and so on), and time yourself.
2. **Conceptual Java and backend**: explain core topics aloud, such as collections, concurrency, Spring, and databases.
3. **System design**: practise the same few designs repeatedly, from requirements to trade-offs.
4. **Behavioural**: prepare stories, then tell each one in about two minutes.

### How to practise well

1. Pick one topic from the question pages.
2. Write the key points of your answer, then close the notes.
3. Explain the answer out loud, as if to an interviewer. Speaking is different from knowing.
4. Time yourself. A rough guide: 10 to 15 minutes for a conceptual question, 30 to 45 minutes for a coding problem, and about 45 minutes for a system design round.
5. Practise with a peer who can interrupt you with follow-up questions.
6. Review what you could not explain, and try again a few days later.

### Prepare questions to ask

Interviewers expect questions from you. Good ones are specific and open:

- How is the team organised, and how do engineers work with product and operations?
- What is a technical problem the team is working on this quarter?
- How do you measure success for this role in the first six months?
- How do incidents get handled, and what does the on-call rota look like?
- What would you most like the next hire to improve?

---

## During the interview

### Technical rounds

**Coding.** Listen to the full problem before you write anything. Ask clarifying questions about input size, edge cases, and the expected output. Talk through a simple approach first, then improve it. State the time and space complexity. Test with a small example, then with edge cases such as empty input, duplicates, and the largest values.

**System design.** Scope the problem before drawing it. Confirm the functional requirements, then the non-functional ones: scale, latency, availability, and consistency. Estimate the load with simple numbers and say which are assumptions. Propose a high-level design, then choose one component to deep-dive when the interviewer shows interest. Name the trade-offs as you make each decision, rather than saving them for the end. The steps are covered in [Architecture and distributed systems, part 2](technical/architecture-and-distributed-part-2.md).

**Conceptual Java and backend questions.** Use a simple structure for each answer:

1. **Direct answer**: state your position in one or two sentences.
2. **Why**: explain the reasoning and the trade-offs.
3. **Example**: give a short piece of code, or a real situation you have seen.
4. **Alternatives**: mention other approaches and when they would be better.

Answering the direct point first shows you understand the question, and the rest of the answer gives the interviewer something to follow up on.

### Communication

- Clarify the question before you start. Restating it in your own words catches misunderstandings early.
- Think aloud. A quiet candidate is hard to assess, even when the answer is right.
- Discuss trade-offs such as speed against readability, consistency against availability, and build cost against operating cost.
- Ask for a hint when you are stuck, and say what you have already tried. This is a sign of good judgement, not weakness.
- If you do not know something, say so, then say how you would find out. "I don't know, but I would check the documentation and test it" is better than a confident wrong answer.
- Keep your energy steady. Interviewers see many candidates, and calm, clear reasoning stands out.

### Handling follow-up questions

Interviewers often push on your answer to see how deep your understanding goes. Treat a follow-up as an invitation to explain more, not as a sign that you were wrong. If you are unsure of the follow-up, reason from first principles and say which parts are guesses.

---

## Behavioural rounds (STAR)

Behavioural questions ask how you acted in a real situation. The STAR structure keeps your answer focused:

- **Situation**: the context, in one or two sentences.
- **Task**: your responsibility or goal in that situation.
- **Action**: the steps you personally took, in the order you took them, phrased in the first person. This part is usually the longest.
- **Result**: the outcome, with numbers where you can (time saved, error rate, latency, users affected), and what you learned.

Keep the whole answer to about two minutes. If the interviewer wants more, they will ask.

A compact template:

> **S:** the context in one sentence. **T:** the goal I owned. **A:** the steps I took, in order. **R:** the measurable result, and what I changed afterwards.

Details of the method, with examples, are in [STAR method](behavioural/star-method.md).

### Stories to prepare

Prepare five or six stories that you can adapt to different questions:

- A hard technical problem you solved, and how you approached it.
- A production incident you diagnosed and fixed, and what you changed to prevent a repeat.
- Something you owned from start to finish.
- A disagreement with a teammate or manager, and how you resolved it.
- A time you worked under a tight deadline or with unclear requirements.
- A mistake you made, what it cost, and what you do differently now.
- A time you led, mentored, or helped a colleague succeed.

### Common behavioural questions

- "Walk me through your background." Aim for 60 to 90 seconds: your current role, your strongest area, and why this role interests you.
- "What has been the hardest project you have delivered?"
- "When did you push back on a teammate or a manager, and what happened?"
- "Describe a mistake you made at work and what came of it."
- "How do you decide what to do first when everything is urgent?"
- "Why do you want this role?" and "Why are you leaving your current role?" Keep the second answer positive, and focus on what you want next rather than what you dislike.

### Tips for behavioural answers

- Lead with the impact, then explain how you achieved it.
- Be specific. "I reduced the p99 latency of checkout from 1.2 seconds to 300 milliseconds" is better than "I improved performance".
- Give credit to others where it is due, while making your own contribution clear.
- For failures, focus on the fix and the prevention, not on blame, including your own.

---

## Practice question formats

| Format | Where to practise | What it tests |
|---|---|---|
| Coding problems | [Coding questions](coding/index.md) | Problem solving, complexity analysis, clean code |
| Conceptual questions | [Technical questions](technical/index.md) | Depth of understanding and clear explanation |
| System design | [Architecture and distributed systems](technical/architecture-and-distributed-part-2.md) and [Practice problems](../learning/19-system-design-fundamentals/practice-problems.md) | Structured thinking and trade-off reasoning |
| Behavioural | [Behavioural questions](behavioural/index.md) | Ownership, communication, and judgement |

---

## After the interview

- Send a short thank-you email within 24 hours, to each person you spoke with if you can.
- Mention one or two specific points from the conversation, so the note is personal.
- State your continued interest in the role, if you still want it.
- If the timeline was not discussed, ask politely when you can expect to hear about next steps.
- Write down the questions you were asked while they are fresh. They are useful for the next round, and for your own practice list.
- Reflect on what went well and what you would change. Update your practice plan based on the gaps you noticed.

---

## Quick recap

- Research the company, and plan practice around each round.
- In each round, clarify first, think aloud, and state trade-offs.
- Answer conceptual questions directly, then explain, give an example, and mention alternatives.
- Use STAR for behavioural questions, with specific results.
- Follow up within a day, and capture the questions you were asked.

**See also:** [Coding questions](coding/index.md) | [Technical questions](technical/index.md) | [Behavioural questions](behavioural/index.md) | [Quick reference](quick-reference.md)
