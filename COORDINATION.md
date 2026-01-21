# Coordination Guide for Hackathon Organizers

This guide provides practical advice for running a distributed hackathon, especially if you're organizing one for the first time.

**Target audience**: Charlie (organizer) and anyone helping with coordination.

---

## Overview: Your Role as Organizer

As organizer, your main jobs are:
1. **Unblock people** - Help when they're stuck
2. **Keep everyone aligned** - Make sure work doesn't conflict
3. **Maintain momentum** - Celebrate progress, adjust plans
4. **Make decisions** - When the team is split, make the call
5. **Protect scope** - Say "no" to scope creep, save ideas for later

**You don't need to**:
- Write the most code (delegation is better)
- Know all the technical details (trust your team)
- Have everything perfectly planned (adapt as you go)

---

## Communication Tools Setup

### Recommended Stack

**Slack or Discord** (Primary communication)
- **#general**: Announcements, daily standups
- **#help**: "I'm stuck" questions
- **#github**: Automated PR/issue notifications
- **#random**: Team bonding, memes
- **#voice**: Voice channel for April 7 (if using Discord)

**GitHub** (Code and tasks)
- **Issues**: Track all work items
- **Pull Requests**: Code review
- **Projects board** (optional): Kanban view of progress
- **Discussions** (optional): Design decisions

**Zoom** (Video meetings)
- March 31 and April 7
- Record sessions for those who can't attend live

**Shared doc** (Google Doc or Notion)
- Meeting notes
- Decision log
- "Parking lot" for ideas that are out of scope

---

## Before March 31: Setup Checklist

### 1 Week Before (March 24)

**Send invitation email** with:
```
Subject: TPC Workshop Reporter Hackathon - March 31 Kickoff

Hi team,

Excited to work with you on the TPC Workshop Reporter project!

📅 Kickoff: March 31, [TIME], [ZOOM LINK]
📍 In-person: April 14-16, [LOCATION]

Before March 31, please:
1. Clone the repo: [GITHUB URL]
2. Complete setup: see pre_hackathon_setup.md
3. Join Slack: [INVITE LINK]
4. Get an LLM API key (OpenAI or Anthropic)

Documents to review:
- README.md - Project overview
- PLAN.md - Timeline and tasks
- pre_hackathon_setup.md - Setup instructions

Questions? Post in #help on Slack.

Looking forward to it!
Charlie
```

### 3 Days Before (March 28)

**Check-in with each participant**:
- "Did you get the repo cloned?"
- "Any issues with setup?"
- "What are you most interested in working on?"

This helps you:
- Identify who needs help before kickoff
- Start thinking about role assignments
- Get a sense of skill levels

### 1 Day Before (March 30)

**Final prep**:
- [ ] Test Zoom link and screen sharing
- [ ] Prepare kickoff slides (10-15 slides max)
- [ ] Print participant list with names/backgrounds
- [ ] Have March 31 agenda ready
- [ ] Create GitHub issues for Priority 1 tasks
- [ ] Prepare role assignment sheet

---

## March 31: Running the Kickoff

### Your Agenda (2-4 hours)

**Before the meeting**:
- Start Zoom 15 min early to test
- Have GitHub and docs open in tabs
- Put phone on silent

**Hour 1: Welcome & Context** [60 min]

```
9:00 - Introductions (20 min)
- Everyone: name, background, timezone, one fun fact
- Charlie: Your background, why this project matters to TPC

9:20 - Project Vision (15 min)
- Show example TPC25 materials (messy reality)
- Show example output report (what we want)
- Explain: "This saves me 20 hours after every conference"

9:35 - Scope Setting (15 min)
- What's IN: workflow pipeline, real TPC25 data
- What's OUT: web scraping, PDF, fancy UI
- Show timeline graphic (March 31 → April 7 → April 14-16)

9:50 - Q&A (10 min)
```

**Hour 2: Technical Walkthrough** [60 min]

```
10:00 - Architecture (20 min)
- Show repo structure on screen
- Explain workflow phases: INGEST → MATCH → SUMMARIZE → EVALUATE → PUBLISH
- Show schema definitions
- Explain: "These are the contracts between components"

10:20 - Development Workflow (20 min)
- Branch naming: feature/your-name/description
- PR process: small PRs, request reviews
- Testing: pytest before you push
- Communication: Slack for questions, GitHub issues for tasks

10:40 - Live Demo of Setup (20 min)
- Screen share: walk through setup steps
- Install dependencies
- Run pytest (even if it fails)
- Import schemas
- Show where docs are
```

**Hour 3-4: Hands-On Setup** [60-120 min]

```
11:00 - Everyone Does Setup (45 min)
- "Let's all get our environments working"
- Stay on Zoom, help people debug
- Use breakout rooms if people have similar issues
- Goal: everyone can run `pytest` by end of this

11:45 - Role Assignment (30 min)
- Ask: "What sounds interesting to you?"
- Assign based on interest + balance of skills
- Give everyone 1-2 tasks from Priority 1 list
- Explain: "You own this, but ask for help anytime"

12:15 - Create GitHub Issues Together (15 min)
- Create issues for each Priority 1 task
- Assign owners
- Explain labels (priority-1, good-first-issue, etc.)

12:30 - Set Expectations for April 1-6 (15 min)
- "Work independently, but post updates daily in Slack"
- "Open PRs early, don't wait for perfection"
- "If stuck for > 1 hour, ask in #help"
- "Goal: 2-3 PRs merged by April 6"

12:45 - Preview April 7 (5 min)
- "We'll spend 6-8 hours integrating everything"
- "Keep Zoom open, work together"
- "By end of day, pipeline should work end-to-end"

12:50 - Wrap Up (10 min)
- Any questions?
- Reminder about Slack check-ins
- "See you in Slack tomorrow, and on Zoom April 7!"
```

**After the meeting**:
- Post summary in #general
- Share recording link
- Thank everyone for joining

---

## April 1-6: Managing Async Work

### Daily Rhythm

**Morning (your time)**:
- Check Slack for any overnight messages
- Review any PRs that came in
- Respond to questions in #help

**Mid-day**:
- Post encouraging message in #general
  - "Great progress on Issue #3, @Alice!"
  - "Reminder: open PRs early even if not done"
  - Share interesting finding or decision

**Evening**:
- Check PR status
- Unblock anyone who's stuck
- Plan next day

### Code Review Guidelines

**You should**:
- Review PRs within 24 hours (or delegate)
- Look for: does it work, is it documented, are tests passing
- Be encouraging: "This looks great! One small suggestion..."
- Approve quickly if it's good enough (don't block on perfect)

**You shouldn't**:
- Require perfection (it's a hackathon)
- Rewrite people's code (suggest and let them do it)
- Block PRs on style issues (save for later)

### When People Get Stuck

**Problem: "I don't know how to do X"**
- Response: "Have you looked at [relevant doc]? Here's a similar example: [link]"
- If they're still stuck after 1 hour: pair with them on Zoom

**Problem: "My PR has been waiting 2 days"**
- Your fault! Review it or find someone else to review
- Apologize and unblock them

**Problem: "I'm blocked on Issue #Y"**
- Ask: "What specifically is blocking you?"
- Options: pair programming, reassign task, provide more context
- Sometimes: "Let's table this and work on Issue #Z instead"

**Problem: "I have no time this week"**
- Response: "No problem! Can you handoff your task to someone?"
- Don't guilt trip - people have lives

### Red Flags to Watch For

🚩 **No one has opened a PR by April 4**
- Action: Post in #general: "Let's see some code! Even drafts are fine"
- Reach out individually: "How's it going? Need any help?"

🚩 **Same person doing everything**
- Action: "Thanks for your energy! Let's make sure others get a chance too"
- Explicitly assign tasks to others

🚩 **Conflicts brewing** (two people implementing the same thing)
- Action: "Hey @Alice and @Bob, looks like you're both working on X. Let's coordinate."
- Quick Zoom call to divide work

🚩 **Scope creep** ("What if we added...?")
- Action: "Great idea! Let's add to post-hackathon list"
- Protect the MVP scope

---

## April 7: Running the Remote Sprint

### Preparation (Day Before)

- [ ] Post reminder in #general with agenda
- [ ] Test Zoom link
- [ ] Review all open PRs and merge what's ready
- [ ] Prepare standup template (see below)
- [ ] Have snacks ready (for yourself!)

### Morning Standup (9:00 AM, 30 min)

**Use this template** (screen share a doc):

```
TPC Workshop Reporter - April 7 Sprint
======================================

Team Status:
- @Alice: Completed Issue #1 (schemas), working on Issue #4 (extractors)
- @Bob: Issue #2 (config) in PR, needs review
- @Charlie: Will review PRs and help with integration
- [etc for each person]

Today's Goals:
1. Get `tpc_reporter ingest` working end-to-end
2. Get all extractors implemented
3. Get basic matching working
4. Write integration test

Blockers:
- Issue #2 PR needs review
- Issue #4: PPTX extraction is tricky, may need help

Team Assignments:
- Team A (Alice + Bob): Ingestion pipeline
- Team B (Charlie + Dana): Extraction + Matching
- Team C (Eve + Frank): Testing
```

**After standup**:
- "Keep Zoom open, mute when working"
- "Unmute to ask questions anytime"
- "Let's check in at noon"

### During the Day

**Your role**:
- Monitor chat and unmute when people ask questions
- Do quick PR reviews
- Help debug when people are stuck
- Keep energy up: "Great progress team!"
- Order food (if remote, remind people to eat)

**Anti-patterns to avoid**:
- ❌ Micromanaging: "Why did you do it that way?"
- ❌ Coding everything yourself
- ❌ Letting people struggle silently for hours
- ❌ Skipping the midday check-in

### Midday Check-in (12:00 PM, 30 min)

**Format**:
1. Everyone demos what works (even if buggy)
2. Celebrate progress
3. Surface blockers
4. Adjust afternoon plan if needed

**Example**: "Team A, show us ingestion!"
- They screen share, run the code
- If it works: applause 👏
- If it breaks: "Okay, let's debug together after lunch"

### End of Day Wrap-Up (4:00 PM, 30 min)

**Goal**: Leave with clear assignments for April 8-13

**Format**:
1. Final demo (even if incomplete)
2. Retrospective:
   - What went well?
   - What was hard?
   - What should we do differently?
3. Assign tasks for April 8-13
4. Set expectations: "No requirement to work every day, but PRs by April 13"

**Post meeting**:
- Post summary in #general
- Share recording
- Thank everyone for their energy

---

## April 8-13: Second Async Period

### Key Differences from April 1-6

- Less structured, more trust
- Focus is on summarization/QA agents
- Okay if some people are less active
- Goal: everything works before April 14

### Your Check-ins

**Monday (April 8)**: 
- Post recap of April 7 progress
- Remind about tasks for the week

**Wednesday (April 10)**: 
- "Halfway point! How's everyone doing?"
- Review what's merged, what's pending

**Friday (April 12)**: 
- "One day until in-person! Let's merge what we can"
- Triage: what can wait until April 14?

---

## April 14-16: In-Person Hackathon

### Space Setup

**What you need**:
- Tables with power outlets
- WiFi password posted visibly
- Whiteboard for diagrams
- Snacks and coffee (important!)
- Music? (ask team preference)

**Seating**:
- Don't assign seats
- Have pairing stations (2 people, 1 screen)
- Have quiet zone for focused work

### Daily Structure

**Each day**:
```
9:00 - Arrival, coffee, standup (30 min)
9:30 - Work session (2.5 hours)
12:00 - Lunch break (1 hour)
1:00 - Work session (2 hours)
3:00 - Break / snacks (15 min)
3:15 - Work session (1.5 hours)
4:45 - Daily wrap-up (15 min)
5:00 - Done! (optional: dinner together)
```

**Flexibility**:
- Some people work better late: "Stay as long as you want"
- Some people need breaks: "Take a walk anytime"
- Pairing vs solo: let people self-organize

### Day 1 (April 14): Integration

**Goal**: Full pipeline runs

**Morning**:
- Identify integration gaps
- Create "integration issues" list
- Assign pairs to each gap

**Afternoon**:
- Fix bugs as they come up
- Test on real TPC25 data
- Document any issues

**Wrap-up**:
- Does it run end-to-end? (even if buggy)
- Biggest blockers for tomorrow?

### Day 2 (April 15): Quality

**Goal**: Outputs are actually useful

**Morning**:
- Review actual summaries produced
- Iterate on prompts
- Tune confidence thresholds

**Afternoon**:
- Documentation pass
- Code cleanup
- Handle edge cases

**Wrap-up**:
- Would we actually use this output?
- What's left for tomorrow?

### Day 3 (April 16): Demo Prep

**Goal**: Ship it!

**Morning**:
- Final bug fixes
- Documentation review
- Test everything one more time

**Afternoon (1-4 PM)**:
- Prepare demo (slides optional, live demo better)
- Record demo video
- Write blog post or README updates

**Demo (4-5 PM)**:
- Show the full pipeline
- Demo actual TPC25 output
- Discuss what you learned
- Celebrate! 🎉

---

## Decision-Making Framework

### When the team agrees
- Great! Move forward

### When the team is split
**Your job**: Make the call
1. Listen to both sides (5 min)
2. Ask: "Which is faster for MVP?"
3. Decide: "Let's go with Option A for now, we can revisit"
4. Document in decision log

**Example**:
- Team split on using OpenAI vs Anthropic
- Your call: "Let's start with OpenAI since more people have keys. We'll make it swappable later."

### When someone wants to add a feature
**Filter through MVP scope**:
- Is it necessary for the demo? → Maybe
- Is it a nice-to-have? → Post-hackathon list
- Will it take > 2 hours? → Probably no

**Response template**:
- "I love this idea! For MVP, let's stick with X. Can you add this to the post-hackathon ideas doc?"

---

## Handling Common Problems

### Someone isn't participating
**Don't**: Call them out publicly
**Do**: DM privately: "Hey, haven't seen you much. Everything okay?"
- They might be busy, sick, or intimidated
- Offer: "Want to pair with me on something simple?"
- Accept: Some people are observers, and that's okay

### Code quality is rough
**Remember**: It's a hackathon, not production
**Do**: Focus on "does it work" not "is it perfect"
**Exception**: If it's so bad it blocks others, refactor it

### Someone is dominating
**Watch for**: One person committing 80% of code
**Do**: "Hey @Alice, you're crushing it! Let's make sure others get hands-on too"
- Assign them to help/review role
- Ask them to pair with junior folks

### You're overwhelmed
**It's okay to**:
- Ask someone else to review PRs
- Delegate the standup
- Take a break
- Reduce scope

**Post in #general**: "I'm swamped today, can @Bob cover PR reviews?"

---

## Communication Templates

### Daily Update Template (for Slack)
```
📅 Day [X] Update

✅ Merged today:
- PR #5: Schema implementation (@Alice)
- PR #7: Config loader (@Bob)

🚧 In progress:
- PR #8: Text extractors (@Charlie)
- Issue #4: Matching logic (@Dana)

🆘 Needs help:
- PR #8: PPTX extraction issue (see thread)

👏 Shoutout: Great debugging by @Alice on the config loader!

Next up: Let's get extractors done by tomorrow
```

### PR Review Template
```
Thanks for this @Alice! 

✅ Code works
✅ Tests pass
✅ Documented

Minor suggestion: [specific change]

Once that's fixed, this is good to merge. Nice work!
```

### Unblocking Template
```
Hey @Bob, saw you're stuck on Issue #X.

Few options:
1. Look at [example/similar code]
2. Simplify: do we need [feature Y] for MVP?
3. Pair with me tomorrow at [time]?

Let me know what would help most!
```

---

## Measuring Success

### You'll know it's going well when:
- ✅ People are posting in Slack without prompting
- ✅ PRs are getting opened and reviewed
- ✅ Team is helping each other (not just asking you)
- ✅ Demos actually work (even if buggy)
- ✅ People are laughing / having fun

### Red flags:
- 🚩 Radio silence in Slack
- 🚩 No PRs being opened
- 🚩 People working in silos
- 🚩 Frustration / tension
- 🚩 You're doing all the work

**If you see red flags**: Have a quick call, reset expectations, ask what would help.

---

## After April 16: Wrap-Up

### Immediately After
- [ ] Thank everyone publicly and individually
- [ ] Share demo recording
- [ ] Collect feedback (Google Form or retro doc)
- [ ] Plan next steps (if any)

### Within 1 Week
- [ ] Clean up repo (merge or close stale PRs)
- [ ] Write blog post or summary
- [ ] Archive or organize Slack
- [ ] Send follow-up email with:
  - What we accomplished
  - Link to demo
  - Future plans
  - Personal thanks

---

## Final Tips for First-Time Organizers

1. **Don't aim for perfection** - Aim for "good enough to be useful"
2. **Celebrate small wins** - Merged PR? Celebrate. Test passes? Celebrate.
3. **Over-communicate** - More updates = less confusion
4. **Trust your team** - They're smart, let them figure things out
5. **It's okay to change plans** - If something isn't working, adapt
6. **Take care of yourself** - Eat, sleep, take breaks
7. **Have fun!** - If you're having fun, the team will too

Remember: The goal isn't a perfect product. The goal is:
- Learn together
- Build something useful
- Have a good time doing it

You've got this! 🚀

---

## Questions?

If you're using this guide and have questions or suggestions, open an issue on GitHub or update this doc with what you learned.

Good luck!
