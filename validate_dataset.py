#!/usr/bin/env python3
"""Validate generated source, graph, persona, scenario, and evaluation integrity."""
import argparse
import hashlib
import json
from pathlib import Path

def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def validate(root):
    errors=[]
    def check(ok,msg):
        if not ok: errors.append(msg)
    docs=load_jsonl(root/"manifests/documents.jsonl")
    by_id={d["document_id"]:d for d in docs}
    text={d["document_id"]:(root/d["path"]).read_text(encoding="utf-8") for d in docs}
    check(len(docs)==2000,"Expected 2000 documents")
    check(len(by_id)==len(docs),"Duplicate document IDs")
    statement_ids={s for d in docs for s in d["statement_ids"]}
    for d in docs:
        check(hashlib.sha256((root/d["path"]).read_bytes()).hexdigest()==d["sha256"],f"Hash mismatch {d['document_id']}")
        check(250<=d["word_count"]<=500,f"Unexpected document size {d['document_id']}: {d['word_count']}")
        check("SYNTHETIC DATA" in text[d["document_id"]],f"Missing synthetic label {d['document_id']}")
        for prev in d["supersedes"]: check(prev in by_id,f"Unknown superseded document {prev}")
    def provenance(p,label):
        did=p.get("document_id")
        check(did in by_id,f"Unknown source document in {label}")
        if did in text:
            check(p["source_quote"] in text[did],f"Source quote mismatch in {label}")
            check(f"### {p['anchor']}\n\n{p['source_quote']}" in text[did],f"Source anchor mismatch in {label}")
        check(p["statement_id"] in statement_ids,f"Unknown statement in {label}")
    entities=load_jsonl(root/"reference_graph/entities.jsonl"); eids={e["id"] for e in entities}
    check(len(entities)>=1000,"Expected >=1000 entities")
    for e in entities:
        check(bool(e["provenance"]),f"Missing entity provenance {e['id']}")
        for p in e["provenance"]: provenance(p,e["id"])
    relations=load_jsonl(root/"reference_graph/relations.jsonl")
    check(len(relations)>=3000,"Expected >=3000 relationships")
    check(len({r["id"] for r in relations})==len(relations),"Duplicate relation IDs")
    for r in relations:
        check(r["subject"] in eids and r["object"] in eids,f"Invalid relation endpoint {r['id']}")
        for p in r["provenance"]: provenance(p,r["id"])
    for f in load_jsonl(root/"reference_graph/facts.jsonl"):
        check(f["entity_id"] in eids,f"Invalid fact entity {f['id']}")
        for p in f["provenance"]: provenance(p,f["id"])
    personas=load_jsonl(root/"personas/synthetic_personas.jsonl")
    check(len(personas)==240,"Expected 240 personas")
    for p in personas:
        check(p["entity_id"] in eids,f"Invalid persona entity {p['id']}")
        for evidence in p["source_evidence"]: provenance(evidence,p["id"])
    questions=load_jsonl(root/"evaluation_private/questions.jsonl")
    gold=load_jsonl(root/"evaluation_private/gold_answers.jsonl")
    check(len(questions)>=120,"Expected >=120 evaluation questions")
    check({q["id"] for q in questions}=={g["id"] for g in gold},"Question/gold mismatch")
    check({"single_hop","multi_hop","temporal","unanswerable"}.issubset({q["category"] for q in questions}),"Missing query categories")
    questions_by_id={q["id"]:q for q in questions}
    for g in gold:
        for sid in g["gold_evidence"]: check(sid in statement_ids,f"Unknown gold evidence {sid}")
        evidence_text="\n".join(text[sid.split(":")[0]].split(f"### {sid.split(':')[1]}\n\n",1)[1].split("\n\n",1)[0] for sid in g["gold_evidence"])
        answer=g["expected_answer"]
        if isinstance(answer,str):check(answer in evidence_text,f"Gold answer absent from cited statements {g['id']}")
        elif isinstance(answer,dict):
            for value in answer.values():check(str(value) in evidence_text,f"Gold answer field absent from cited statements {g['id']}")
        elif answer is None:check(not g["answerable"] and not g["gold_evidence"],f"Invalid unanswerable case {g['id']}")
        q=questions_by_id[g["id"]]
        if q["as_of"]:
            for sid in g["gold_evidence"]:
                check(by_id[sid.split(":")[0]]["published_at"]<=q["as_of"],f"Gold evidence from future relative to as_of {g['id']}")
    for name,count in [("smoke",20),("medium",200),("stress",2000)]:
        m=json.loads((root/f"manifests/{name}.json").read_text())
        check(len(m["documents"])==count,f"Wrong {name} profile size")
        check(len({d["document_id"] for d in m["documents"]})==count,f"Duplicate profile documents {name}")
        for d in m["documents"]:
            check(d["document_id"] in by_id,f"Unknown profile document {name}")
            check(d["path"].startswith("corpus/documents/"),f"Unsafe ingestion path {d['path']}")
    scenarios=list((root/"scenarios").glob("*/scenario.json"))
    check(len(scenarios)==4,"Expected four scenarios")
    for path in scenarios:
        s=json.loads(path.read_text())
        check(s["engine_native_format"] is False,"Incorrect engine-native claim")
        for did in s["source_documents"]: check(did in by_id,f"Invalid scenario source {did}")
        for eid in s["actor_entity_ids"]: check(eid in eids,f"Invalid scenario actor {eid}")
        check((path.parent/"canonical_seed.txt").exists(),"Missing scenario seed")
    manifest=json.loads((root/"dataset_manifest.json").read_text())
    for entry in manifest["files"]:
        p=root/entry["path"]
        check(p.exists(),f"Missing manifest file {entry['path']}")
        if p.exists():check(hashlib.sha256(p.read_bytes()).hexdigest()==entry["sha256"],f"Manifest hash mismatch {entry['path']}")
    report={"status":"passed" if not errors else "failed","errors":errors,"counts":manifest["counts"],"checks":["document hashes","entity and relation provenance","exact source quotes and anchors","temporal reference integrity","persona evidence","held-out evaluation references","ingestion profile exclusion","scenario references","file manifest hashes"],"limitations":["No Ollama inference or MiroFish simulation was executed.","No semantic extraction quality benchmark was run."]}
    (root/"validation_report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    return 0 if not errors else 1

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--root",type=Path,default=Path(__file__).parent);args=ap.parse_args()
    raise SystemExit(validate(args.root.resolve()))
