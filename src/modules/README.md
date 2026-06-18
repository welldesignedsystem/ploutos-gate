# modules

Domain packages for `ploutos-gate` project. Each subdirectory is a self-contained Python package.

| Package | Description |
|---------|-------------|
| `probe/` | Competitor-finding term generator — crawl, profile, LLM generates terms with reasoning |
| `llm/` | Provider-agnostic LLM config, agent factory, and async client |

Packages are importable directly (no `modules.` prefix):

```python
from probe.client import probe
from llm.models import LLMConfig
```
