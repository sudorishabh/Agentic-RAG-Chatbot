"""Answer generation: context blocks -> a cited answer.

Reads ``ContextBlock`` from :mod:`app.core.models.context` and never imports a
retrieval implementation module. Prompt text lives in :mod:`.prompts`; the
answer/verification flow in :mod:`.answerer`, :mod:`.faithfulness`,
:mod:`.sections`, :mod:`.redundancy`, :mod:`.answer_plan` and
:mod:`.date_claims`.
"""
