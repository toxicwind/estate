---
name: research
description: Use Exa for multi-step research on a topic.
parameters: [topic]
---
Call `exa_search({query:"{{ topic }}", num_results:8})`. Summarize the three
most relevant sources with URLs. If EXA_API_KEY is unset, fall back to Ralph's
`web_search`.
