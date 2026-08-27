"""Context assembly: selected candidates -> numbered blocks the LLM is shown.

The last stage of the read path. :mod:`.builder` decides which candidate text is
admitted, in what order, and with what page attribution; :mod:`.citations`
describes those same blocks back to the user.

``ContextBlock`` itself lives in :mod:`app.core.models.context`, not here, so
generation never has to import a retrieval implementation module.
"""
