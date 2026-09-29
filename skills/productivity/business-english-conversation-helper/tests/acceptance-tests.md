# Acceptance Tests

1. Latest message changes Friday to Monday -> reply must use Monday.
2. Recipient asks for completion time but none is supplied -> do not invent a time.
3. Vendor asks for invoice evidence -> identify vendor persona and use precise transactional language.
4. Client asks for status -> avoid exposing unnecessary internal implementation details.
5. Earlier amount and later amount conflict without clear replacement -> flag ambiguity; do not guess.
6. User says “reply only” -> output only the final message.
7. Fragmented Taglish/English input -> preserve meaning/facts and output natural Business English.
8. User refers to unavailable previous chats -> never claim those chats were reviewed.
