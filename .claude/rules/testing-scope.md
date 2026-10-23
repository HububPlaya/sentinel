---
description: Two different kinds of "testing this platform" -- platform-internal vs. customer-capability -- and how to tell them apart when scoping work.
paths: ["**/*"]
---

# Platform-internal testing vs. customer-capability testing

This repo is a platform meant to onboard multiple customer app teams, but right now has only one
real app (`snack-recommender`), managed by the same person building the platform itself. That
makes it easy to conflate two genuinely different concerns -- keep them separate:

- **Platform-stack-internal testing**: validating changes to this repo's own `infra/`/`pipeline/`
  CDK code before they reach `main` (e.g. #344's version-label bug, `cdk synth`/`cdk diff` checks).
  This is the platform team's own CI concern, same as any codebase's.
- **Customer-capability testing**: validating the *features the platform offers to onboarded app
  teams* (ephemeral per-PR environments, scoped test credentials -- #260/#262/#263, under Epic
  #33 "Test Execution Infrastructure," explicitly "for app teams") -- these are product
  capabilities for customers, not this repo's own engineering practice.

Until a real second app team onboards, **a deliberately simulated second test app stands in for
a real customer tenant** to validate multi-tenant capabilities (concurrent-PR isolation, etc.)
rather than guessing at what a hypothetical future customer would need. When scoping a story,
say explicitly which of the two categories it belongs to -- don't let "we only have one app"
become a reason to quietly fold a customer-capability story into platform-internal work, or vice
versa.
