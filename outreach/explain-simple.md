# The Thesis in Plain Words

For explaining the work out loud — to the professor, in a talk, or to someone outside the field.
The formal version is in [`thesis.md`](thesis.md); this says the same thing as a story.

---

## The problem, as a story

You tell your AI work assistant: *"Email the landlord to renew our office lease."*

To write that email it searches your company's files and Slack, and finds three things:

1. The **official lease document** — real, and fine to discuss with the landlord.
2. An **internal memo**: "our absolute maximum is $54/sqft, walk away above that." Real, but **secret**.
3. A **Slack message** from HR: "we're probably cutting headcount, so we'd only need ~13,000 sqft." **Unconfirmed gossip.**

The assistant treats all three the same, because once information is in front of it, it assumes the information is both fine to share and true. So it writes an email that tells the landlord your maximum price — destroying your negotiating position — and states the 13,000 sqft figure as if it were company policy, when it was just chatter.

## Those are two different mistakes

- It **said something it shouldn't have said.** A secret got out.
- It **trusted something it shouldn't have trusted.** Gossip got promoted into an official commitment.

Existing research (CI-Work) measures only the first. The second, nobody is even counting.

Note the first mistake depends on **who is receiving it**: telling your own boss the walk-away price is completely fine. It's only wrong because it went to the landlord. So this is about *appropriateness*, not secrecy.

## Our fix

Put a **checkpoint right before the assistant hits send** — like a mailroom clerk who reads every outgoing letter. For each fact in the draft the clerk asks two questions:

- *Is this too secret to send to **this particular** person?* → cut it.
- *Is this too unreliable to state as fact?* → cut it, or soften it to "I've heard, unconfirmed…"

Those two questions aren't invented. They are two well-established security rules from the 1970s — **Bell-LaPadula** (keeps secrets from leaking out) and **Biba** (keeps unreliable data from being treated as trusted) — re-applied to AI agents. The second paper (Tian & Song) is where we get the idea of applying them **continuously**, re-checking every request rather than trusting anything by default. That's what "zero trust" means here: *never trust the context.*

## Why this isn't obvious, and why it might work

People already tried the simple thing: telling the AI "be careful, don't share sensitive stuff." It helps a little, but it makes the assistant so nervous that it starts omitting the information you actually needed — the email becomes safe and useless. (In CI-Work's numbers: violations dropped from 27.8% to 21.3%, but usefulness fell from 93% to 81%.)

Our approach doesn't make the whole model nervous. It removes **specific identified items** and leaves everything else alone. So the email should stay useful.

## The whole bet in one sentence

We can make these agents meaningfully safer **without making them useless** — and we can catch a kind of failure nobody is currently measuring at all.

---

## How this connects to SafeLattice

This project is the natural sibling of [`claw-eval-safelattice`](https://github.com/nilakarthikesan/claw-eval-safelattice) (CS 8903, also under Prof. Madisetti):

| | Model | Protects | Question it answers |
|---|---|---|---|
| **SafeLattice** | Bell-LaPadula | confidentiality | "is this too secret to release?" |
| **This project** | Biba | integrity | "is this too unreliable to rely on?" |

Bell-LaPadula and Biba are the two halves of the classic multilevel-security pair — one blocks secrets flowing down, the other blocks untrusted data flowing up. SafeLattice applied the first half to agent *evaluation*; this applies the second half, plus zero-trust enforcement, to agent *defense*. Together they're a coherent research arc rather than two unrelated projects, which is a useful thing to point out to the professor.
