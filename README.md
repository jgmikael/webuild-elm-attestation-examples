# WE BUILD ELM / JSON-LD / W3C VC exercises

Two parallel exercises created 27 October 2026:

- [Microcredential walkthrough](microcredential/microcredential-exercise.md): a fictional 3-ECTS Applied Data Ethics award.
- [Verified Skill walkthrough](verified-skill/verified-skill-exercise.md): fictional competent compressor-operation skill, assessed by an identified third party.

Each folder contains the original rulebook-oriented semantic SHACL profile, a W3C VC 2.0 derivative, a standalone extension context, an unsigned example credential and validation results. The context object is embedded inline in each example after the official W3C v2 context.

The W3C examples are proposed alternate representations. The current source rulebooks define SD-JWT VC issuance and do not yet adopt these W3C encodings. The original profiles require SD-JWT fields vct, iat and cnf; the W3C derivatives intentionally disconnect that transport requirement and retain the domain constraints. Neither example contains a fabricated proof or holder-binding key.

## Run the exercises

Use Python 3.10 or later in a virtual environment:

```sh
python -m venv .venv
# Activate the environment for your operating system, then:
python -m pip install -r requirements.txt
python validate_examples.py
```

The validator uses the included official W3C v2 context snapshot, so validation does not fetch remote contexts or example.org identifiers. It checks JSON-LD expansion, SHACL meta-validation, application constraints, undefined populated keys, RDF round-trip equivalence, expected original-profile transport failures, and representative positive/negative mutations.

`validation-results.json` in each exercise records the development checks; the runnable validator repeats the main checks and a smaller representative mutation suite. Live code-list membership, ESCO alignment, genuine accreditation, assessor independence, actual audits, signatures and issuer trust are outside these checks.

Read the walkthrough before modifying nested values: a context maps terms, but does not automatically restructure flat claims or convert numbers to durations.

## Sources

- Microcredential rulebook: https://github.com/webuild-consortium/webuild-attestation-rulebooks-catalog/tree/main/rulebooks/rb-microcredential — v1.0, 2026-10-20; blob 4b5a058373107f8401cac95940179474e6459bac.
- Verified Skill rulebook: https://github.com/webuild-consortium/webuild-attestation-rulebooks-catalog/tree/main/rulebooks/rb-verified-skill — v0.2, 2026-10-05; blob 6c6883cf8510fdc31e80f7d32e58be4a58faed30.
- ELM 3.3.1: https://europa.eu/europass/elm-browser/documentation/3-3-1/rdf/ontology/documentation/index-en.html.
- W3C VC 2.0: https://www.w3.org/TR/vc-data-model-2.0/.
- Official base context snapshot: https://www.w3.org/ns/credentials/v2 (retrieved 27 October 2026; included unchanged for reproducible validation).
