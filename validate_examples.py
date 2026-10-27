#!/usr/bin/env python3
"""Validate the two illustrative credentials without fetching remote contexts.
Run: python validate_examples.py
Dependencies: pip install -r requirements.txt
This checks JSON-LD/RDF/SHACL; it does not verify signatures or issuer trust.
"""
import copy
import json
from pathlib import Path
from rdflib import Graph, Literal, Namespace, RDF, SH, XSD
from rdflib.compare import isomorphic
from pyld import jsonld
from pyshacl import validate

ROOT = Path(__file__).resolve().parent
BASE_URL = 'https://www.w3.org/ns/credentials/v2'
BASE_CONTEXT = json.loads((ROOT / 'w3c-vc-v2-context.json').read_text())
ELM = Namespace('http://data.europa.eu/snb/model/ontology/')
CRED = Namespace('https://www.w3.org/2018/credentials#')
DCT = Namespace('http://purl.org/dc/terms/')


def loader(url, options=None):
    if url != BASE_URL:
        raise ValueError(f'Unexpected remote context: {url}')
    return {'contextUrl': None, 'documentUrl': url, 'document': BASE_CONTEXT}


def rdf_graph(document):
    nq = jsonld.to_rdf(document, options={
        'documentLoader': loader, 'format': 'application/n-quads'})
    return Graph().parse(data=nq, format='nquads')


def test(exercise):
    folder = ROOT / exercise
    vc = json.loads((folder / f'{exercise}-vc-example.jsonld').read_text())
    context = json.loads((folder / f'{exercise}-context.jsonld').read_text())
    assert vc['@context'] == [BASE_URL, context['@context']]
    assert 'VerifiableCredential' in vc['type']
    assert vc['issuer']['id'] and vc['credentialSubject']
    assert 'proof' not in vc, 'Examples deliberately contain no fabricated proof.'
    expanded = jsonld.expand(vc, options={'documentLoader': loader})
    graph = rdf_graph(vc)
    shape = Graph().parse(folder / f'{exercise}-vc2.shacl.ttl')
    conforms, report, text = validate(
        graph, shacl_graph=shape, meta_shacl=True, allow_warnings=True)
    assert conforms, text
    assert not list(report.subjects(SH.resultSeverity, SH.Warning)), text
    compacted = jsonld.compact(expanded, vc['@context'], options={'documentLoader': loader})
    assert isomorphic(graph, rdf_graph(compacted)), 'RDF round-trip changed meaning.'
    # Reject undefined application properties rather than silently dropping them.
    defined = set(context['@context']) | {
        'id', 'type', 'issuer', 'credentialSubject', 'name', 'description',
        'validFrom', 'validUntil', 'evidence', '@context', '@value', '@language'}
    def keys(obj):
        if isinstance(obj, list):
            for value in obj:
                yield from keys(value)
        elif isinstance(obj, dict):
            for key, value in obj.items():
                if key != '@context':
                    yield key
                    yield from keys(value)
    assert not set(keys(vc)) - defined
    namespace = 'microcredential' if exercise == 'microcredential' else 'verified-skill'
    extension = Namespace(f'https://example.org/webuild/{namespace}/profile/')
    original = Graph().parse(folder / f'{exercise}-elm.shacl.ttl')
    ok, original_report, original_text = validate(
        graph, shacl_graph=original, allow_warnings=True)
    assert not ok, 'The original profile should require SD-JWT metadata.'
    assert set(original_report.objects(None, SH.resultPath)) == {
        extension.vct, extension.iat, extension.cnf}, original_text
    print(f'{exercise}: expansion, meta-SHACL, semantic SHACL, key coverage, '
          f'RDF round-trip PASS ({len(graph)} triples)')

    def check(name, mutation, expect=False):
        changed = Graph() + graph
        mutation(changed)
        passed, _, message = validate(changed, shacl_graph=shape, allow_warnings=True)
        assert passed == expect, f'{exercise}: {name}\n{message}'
        print(f'  PASS: {name}')

    if exercise == 'microcredential':
        spec = next(graph.subjects(RDF.type, ELM.LearningAchievementSpecification))
        point = next(graph.subjects(RDF.type, ELM.CreditPoint))
        assessment = next(graph.subjects(RDF.type, ELM.LearningAssessment))
        check('zero ECTS rejected', lambda g: g.set((point, ELM.point, Literal('0'))))
        check('ECTS plus duration rejected', lambda g: g.add(
            (spec, ELM.volumeOfLearning, Literal('PT8H', datatype=XSD.duration))))
        def alternative(g):
            g.remove((spec, ELM.creditPoint, None))
            g.add((spec, ELM.volumeOfLearning, Literal('PT8H', datatype=XSD.duration)))
        check('duration-only alternative accepted', alternative, True)
        check('assessment after issuance rejected', lambda g: g.set(
            (assessment, DCT.issued, Literal('2026-06-16T00:00:00Z', datatype=XSD.dateTime))))
    else:
        claim = next(graph.subjects(RDF.type, ELM.LearningAchievement))
        spec = next(graph.subjects(RDF.type, ELM.LearningAchievementSpecification))
        assessment = next(graph.subjects(RDF.type, ELM.LearningAssessment))
        check('EQF cannot replace Dreyfus proficiency', lambda g: g.set(
            (claim, extension.skillProficiencyLevel, Literal('EQF-6'))))
        check('proficiency cannot replace QA level', lambda g: g.set(
            (assessment, extension.qualityAssuranceLevel, Literal('expert'))))
        check('zero hours rejected', lambda g: g.set(
            (spec, ELM.volumeOfLearning, Literal('PT0H', datatype=XSD.duration))))
        check('audited level without audit support rejected', lambda g: g.set(
            (assessment, extension.qualityAssuranceLevel, Literal('audited-assessment'))))
        def remove_third_party(g):
            g.remove((assessment, ELM.assessedBy, None))
            for evidence in list(g.objects(assessment, extension.assessmentEvidence)):
                g.remove((evidence, DCT.creator, None))
        check('third-party assessment without identified third party rejected', remove_third_party)
        check('optional workload can be omitted', lambda g: g.remove(
            (spec, ELM.volumeOfLearning, None)), True)


if __name__ == '__main__':
    for item in ['microcredential', 'verified-skill']:
        test(item)
    print('All checks passed. Both example credentials remain unsigned.')
