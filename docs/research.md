# Academic Research & Empirical Benchmarking Framework

## Comparative Study: Direct Cloud API Integration vs. Model Context Protocol (MCP)

This project forms the empirical core of a final-year Computer Science research inquiry:
**"Quantifying Architectural Overhead and Engineering Ergonomics in Multi-Cloud Tool Retrieval: Direct APIs vs. Model Context Protocol"**

---

## 1. Research Questions

1. **RQ1 (Latency & Overhead)**: What is the round-trip latency overhead introduced by serializing tool definitions and responses through an MCP layer compared to direct provider API invocations?
2. **RQ2 (Maintainability & Extensibility)**: How many lines of code and configuration changes are required to add an $N^{\text{th}}$ cloud storage provider under traditional tight coupling versus under an MCP provider abstraction?
3. **RQ3 (LLM Grounding & Accuracy)**: Does an MCP standardized schema improve LLM parameter prediction accuracy compared to varied proprietary API schemas?

---

## 2. Experimental Harness Structure

Located in `/research`:
- `benchmarks/`: Automated benchmark scripts comparing execution time, memory, and payload size.
- `traditional_api/`: Reference implementations calling Google Drive, Microsoft Graph, and Dropbox directly without MCP.
- `mcp_implementation/`: Implementations utilizing MCP SDK v2 tool calls.
- `datasets/`: Standardized synthetic queries and test file corpora (PDFs, DOCX, TXT with invoices, resumes, code, and offer letters).
- `results/`: CSV outputs and automated visualization generation for academic reports and viva presentation.

---

## 3. Benchmark Metrics Tracked

| Metric | Direct API | MCP Layer | Delta / Ratio |
|---|---|---|---|
| Single Query Latency (ms) | $T_{\text{direct}}$ | $T_{\text{mcp}}$ | $T_{\text{mcp}} - T_{\text{direct}}$ |
| Memory Footprint (MB) | $M_{\text{direct}}$ | $M_{\text{mcp}}$ | Overhead ratio |
| Lines of Integration Code | $LOC_{\text{direct}}$ | $LOC_{\text{mcp}}$ | Engineering complexity |
| Module Coupling Index | High | Low | Structural isolation |
| LLM Tool Parameter Errors | Rate | Rate | Accuracy gain |
