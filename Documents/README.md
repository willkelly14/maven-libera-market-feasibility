# Documents Database

Each document used in or produced for the market feasibility study is registered in `documents_index.yaml` and has its content stored as a markdown file in this directory.

## Structure

```
Documents/
├── README.md
├── documents_index.yaml          ← registry of all documents
├── macro_context_data_sources.md ← content file
├── supply_side_research_plan.md  ← content file
└── ...
```

## Adding a Document

1. Create a `.md` file in this directory with the document content
2. Add an entry to `documents_index.yaml` pointing to it
3. In the Fact Database YAML files, reference the document ID in the `document` field

## Document Types

| Type | Description |
|------|-------------|
| `section_draft` | Draft text for a feasibility study section |
| `data_sources` | Collated source/reference sheet |
| `research_plan` | Research methodology or execution plan |
| `research_report` | Company or facility research report |
| `source_reference` | External source document summary |
