# remmeh
a tui LLM chat and research tool

# Phase 1 - Features
- Using Python 3.12, uv, ty, ruff, Textual (library)
- Well-designed test coverage
- Integration with OpenRouter endpoints, fetching the models automatically
- Chat session history stored locally
- All messages, including thinking blocks stored locally as well for debugging
- Formatting for sent messages and responses, some form of Markdown formatting and coloring
- Sessions can be organized in folders for organization
- Command pallet allows for all functionality configuration
- Hot key configuration and rebinding for common features
  - Changing models
  - Starting new conversations
- Models can be marked as default (the one we start with) or Favorited (the ones we can see at the top of the model list)

## Phase 1 - UI Layout
- Bottom panel dedicated to user input, only 3 line height, but has scrolling
- Right side slides in and out to show session lists

# Phase 2 - Features (Research)
- Ability to search for web pages and fetch web content
- Custom integrations for specific web sources (eg: Github, Pypi, other LLM friendly search content) for easy researching

# Phase 3 - Features (Personalities)
- Ability to create and edit custom agent personalities and configuration, can summon the agent personalities by @-mentioning them

# Phase 4 - Features (Conversation Splits)
- Split conversations into new conversations with different agents
- Edit previous messages by the user or the agent to modify the outcome
- Compare two conversations via LLM to understand them
