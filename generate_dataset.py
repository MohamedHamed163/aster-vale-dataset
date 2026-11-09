#!/usr/bin/env python3
"""Generate a deterministic fictional enterprise corpus using only Python's stdlib."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

SEED = 731902
SCHEMA = "macos-ai-synthetic-corpus/1.0"
COMPANY = "Aster Vale Systems (fictional)"
BASE = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)
DOMAINS = [
    ("document discovery", "research teams", "find approved source passages", "irrelevant search results"),
    ("warehouse planning", "warehouse coordinators", "reserve loading slots", "overlapping reservations"),
    ("learning operations", "course administrators", "publish assessment schedules", "outdated course versions"),
    ("field maintenance", "maintenance dispatchers", "assign repair visits", "missing equipment histories"),
    ("supplier onboarding", "procurement teams", "compare supplier submissions", "incomplete verification records"),
    ("design collaboration", "design reviewers", "approve annotated design revisions", "conflicting review comments"),
    ("event operations", "event coordinators", "allocate exhibitor resources", "late resource changes"),
    ("energy reporting", "facilities analysts", "review meter summaries", "delayed measurement batches"),
    ("subscription support", "support specialists", "reconcile customer entitlements", "stale entitlement caches"),
    ("delivery coordination", "delivery planners", "confirm delivery windows", "unacknowledged route changes"),
]
TYPE_SPECS = [
 ("charter", "Project charter", "The charter fixes the business problem and names the accountable people. The sponsor will assess the pilot using completed user tasks, documented corrections, and unresolved exceptions. Scope changes must reference this charter so the team can distinguish a required outcome from a convenient addition.", "An implementation shortcut is acceptable only when the original task remains observable to the pilot coordinator. The team will retain a manual fallback, document its trigger, and record who used it. A polished interface alone cannot close an acceptance item."),
 ("architecture", "Architecture decision", "The architecture separates the user interface, domain services, operational storage, and background processing. Typed boundaries prevent a change in a document parser from silently changing account records. Each request carries a correlation identifier so a reviewer can follow the path through the components.", "The team considered a single synchronous request path and rejected it for long operations. The selected design records a job before work begins, returns an identifier, and publishes progress. On retry, completed external actions must be reconciled before another action is attempted."),
 ("supplier", "Supplier agreement note", "This procurement note records the selected supplier and the service being purchased. Delivery acceptance requires a reproducible sample, versioned configuration, and a named support contact. The contract owner will keep operational support separate from product approval so neither decision is implied by the other.", "An alternate source may be evaluated if the primary delivery misses the agreed checkpoint. Evaluation must use the same acceptance sample and preserve the original supplier's evidence. The team must record any difference in recurring cost, maintenance effort, and recovery procedure before changing vendors."),
 ("capacity", "Capacity and queue plan", "The capacity estimate is a planning assumption for a synthetic pilot, not a measured production result. The operations team will measure queue wait separately from processing time. Large jobs receive explicit progress updates, and a cancellation request must prevent additional work from being scheduled.", "Capacity changes are reviewed against the same workload manifest. A faster average is insufficient if a small group of requests repeatedly times out. The team will publish sample counts, error counts, and the conditions of each run alongside the summary so the result can be independently checked."),
 ("research", "User research brief", "The research session focuses on a complete task rather than opinions about interface appearance. Participants receive the same starting information and describe where they hesitate, what they expect, and what evidence they need before acting. Observers distinguish a participant statement from their own interpretation.", "The findings are limited to this synthetic pilot group. They should guide a follow-up experiment rather than be generalized to every customer. Each design proposal must identify the observed difficulty it addresses, a measurable outcome, and a way to reverse the change if it adds confusion."),
 ("requirements", "Requirements specification", "The specification defines a normal path, an empty state, a validation failure, and a recoverable service error. Every requirement has an owner and an observable outcome. The implementation team may change internal details, but a changed user-visible behavior requires an explicit decision record.", "Dependencies are tracked at the interface level so work can proceed in parallel. A requirement is incomplete when its data source, refresh behavior, or error response remains unspecified. The reviewer will ask for those details before treating a screen mockup as an implementable agreement."),
 ("implementation", "Implementation checkpoint", "The checkpoint describes work against the agreed interface contract. The frontend may use fixtures while the service is being implemented, but the fixtures must be generated from the same schema. Shared files have one owner during parallel work, and any proposed contract change is reviewed before integration.", "Completion means the integrated behavior satisfies the acceptance checks with the real service boundary in place. A branch that compiles is useful progress, but it does not establish the task outcome. The team records the remaining limitations and the exact revision associated with each verification artifact."),
 ("security", "Access review", "The review follows data from the authenticated user through lookup, processing, and export. Resource ownership is checked by application code before retrieval. Text inside an imported document is treated as content and cannot grant a new permission or redirect a privileged tool invocation.", "The reviewer tests an allowed request, a request for a different workspace, and a malformed identifier. Rejected actions remain visible in the local audit record without exposing protected content. Credentials are stored outside the document corpus and are excluded from diagnostic attachments."),
 ("accessibility", "Accessibility review", "The review covers keyboard navigation, focus order, readable labels, and useful announcements when work finishes or fails. Loading indicators explain what is happening and offer cancellation where cancellation is supported. Color is supplementary information rather than the only way to distinguish outcomes.", "The pilot coordinator will repeat the primary task with reduced motion and a larger text setting. A visual improvement is accepted only after the task remains understandable in those modes. Any unresolved issue is recorded with a reproduction path and the specific interaction it affects."),
 ("acceptance", "Acceptance test plan", "The acceptance plan is written before the final implementation is evaluated. It includes representative examples, boundary conditions, and a case that must stop because the required evidence is missing. The expected outcome is stored separately from the input material supplied to the implementation.", "A failed check remains failed even when the interface produces a plausible explanation. Reviewers inspect the actual record, response, or artifact. Tests that merely repeat the implementation logic are replaced by checks against the user outcome and the agreed external contract."),
 ("pilot", "Pilot feedback report", "The pilot feedback separates observed behavior, participant comments, and proposed changes. Repeated comments are grouped without erasing the individual source records. The customer representative selects one problem for the next iteration so the team can measure an effect rather than changing every variable at once.", "A satisfactory demonstration does not prove that every workflow is ready. The report records the sample conditions and the tasks that were not exercised. Follow-up work must preserve the baseline configuration and identify whether a proposed improvement changes quality, response time, or operational effort."),
 ("incident", "Incident investigation", "The investigation follows a timeline of recorded events and distinguishes the triggering condition from contributing factors. Recovery actions are listed with their observed effects. An explanation is marked as a hypothesis when the available records cannot establish the proposed connection.", "The team will preserve the affected sample and repeat the failure in an isolated test. A successful retry alone is insufficient to prove a repair. The corrective action must address the documented cause and include a regression check that would have exposed the original behavior."),
 ("change", "Change proposal", "This document proposes a change; it does not authorize a new release date. The owner describes the problem, options, expected effect, and rollback path. Stakeholders can approve a narrower experiment without approving the full implementation, and those decisions are recorded separately.", "The proposal compares keeping the current behavior, making the targeted change, and postponing the feature. Each option includes dependencies and a way to observe success. The release authority will decide after reviewing the evidence, while the existing baseline remains in force until then."),
 ("baseline", "Baseline release schedule", "This baseline is an authoritative planning record as of its publication time. It establishes the planned launch date and the dependencies that must be ready before launch. It can be superseded only by a later release decision that explicitly references this record.", "The schedule is a plan, not proof that the release occurred. Task owners must report blocked dependencies early and preserve the reason for each date change. Historical questions should use the version that was effective at the requested time rather than applying today's plan retroactively."),
 ("risk", "Risk review", "The risk review considers likelihood and impact as qualitative judgments for this fictional exercise. Every material risk has an owner, a trigger for escalation, and a proposed response. The report keeps uncertainty visible rather than presenting an invented probability as a measured forecast.", "Several stakeholders may disagree about an appropriate response. The next review should compare their assumptions against the same evidence bundle. Simulations may explore these disagreements, but a simulated outcome must retain its scenario label and cannot replace a recorded business decision."),
 ("budget", "Budget checkpoint", "The checkpoint distinguishes an approved budget from spending and from an estimate of future cost. The finance reviewer records the assumptions behind each amount. A technical improvement may still require a separate funding decision if it changes support effort or recurring charges.", "The team will compare options over the same planning period and avoid combining totals with different scopes. Any missing estimate is labeled unavailable. Changes in project scope must be reflected in both the delivery plan and this cost record before a final recommendation is made."),
 ("release", "Revised release decision", "This decision supersedes the earlier baseline release schedule. The authority reviewed pilot evidence, dependency readiness, and recovery preparation before approving the revised plan. It records a planned date and does not assert that the product has already launched.", "Historical queries must retain the previous baseline as evidence of the earlier plan. The current interface should show the revised date and link to the superseded record. Downstream teams receive the change together with its reason, owner, and the tasks affected by the revision."),
 ("communications", "Communication plan", "The communication plan uses a consistent evidence packet for support, sales, and the pilot customer. Messages distinguish a committed decision from a proposed option. A draft can be reviewed internally without implying authorization to send it to an external recipient.", "Updates should explain what changed, who is affected, and what action is required. The team will avoid repeating obsolete dates from a copied announcement. Every outgoing version references the current release decision and retains the source material needed to correct an error promptly."),
 ("support", "Support readiness note", "Support readiness requires a reproducible troubleshooting path and access to the relevant operational records. The agent or employee should identify missing evidence before making a diagnosis. Escalations include the observed behavior, expected behavior, customer impact, and references that another person can inspect.", "The support team practices both a normal resolution and a case that must be escalated. The exercise records whether the procedure was sufficient, whether the required tools were available, and where the handoff lost context. Improvements are versioned so later runs can be compared fairly."),
 ("handover", "Operational handover", "The handover names the team responsible for routine operation and the people who can decide on a change. It includes the current plan, known limitations, recovery procedure, and locations of verification artifacts. Ownership is explicit so an alert does not depend on informal personal knowledge.", "The receiving team repeats a representative task and a recovery exercise before accepting the handover. Remaining work is listed with a measurable completion condition. The project remains traceable after handover because source documents, decisions, and supersession links keep their original identifiers."),
]

def utc(d):
    return d.isoformat(timespec="seconds").replace("+00:00", "Z")

def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def generate(root, seed=SEED):
    rng = random.Random(seed)
    root.mkdir(parents=True, exist_ok=True)
    docs_dir = root / "corpus" / "documents"
    docs_dir.mkdir(parents=True, exist_ok=True)
    entities = {}
    relations = []
    facts = []
    docs = []
    by_doc = {}

    def entity(eid, kind, name, **attrs):
        entities[eid] = {"id": eid, "type": kind, "name": name, "synthetic": True,
                         "attributes": attrs, "provenance": []}
        return eid

    company = entity("ORG-001", "organization", COMPANY, domain="astervale.example")
    teams = [entity(f"TEAM-{i+1:03}", "team", f"Delivery Team {i+1:02}") for i in range(24)]
    first = ["Ava", "Milo", "Nora", "Ezra", "Lina", "Owen", "Maya", "Theo", "Iris", "Noel", "Sana", "Eli"]
    last = ["Cedar", "Vale", "Brook", "Reed", "Stone", "Fern", "Grove", "Linden", "Rowan", "Harbor"]
    people = [entity(f"PERSON-{i+1:03}", "person", f"{first[i%12]} {last[(i//12)%10]} ({i+1:03}, synthetic)") for i in range(240)]
    suppliers = [entity(f"SUPPLIER-{i+1:03}", "supplier", f"Fable Supply {i+1:02}", domain=f"fablesupply{i+1:02}.example") for i in range(50)]
    projects = []
    for p in range(100):
        domain, audience, task, failure = DOMAINS[p % len(DOMAINS)]
        start = BASE + timedelta(days=p % 28)
        budget = 40000 + rng.randrange(0, 31) * 1500
        project = {
            "index": p, "project": entity(f"PROJECT-{p+1:03}", "project", f"Lumen Initiative {p+1:03}"),
            "product": entity(f"PRODUCT-{p+1:03}", "product", f"Lumen {domain.title()} {p+1:03}"),
            "customer": entity(f"CUSTOMER-{p+1:03}", "customer", f"Cedar Pilot Organization {p+1:03}", domain=f"cedarpilot{p+1:03}.example"),
            "supplier": suppliers[p % 50], "team": teams[p % 24],
            "owner": people[(3*p) % 240], "sponsor": people[(3*p+1) % 240], "reviewer": people[(3*p+2) % 240],
            "components": [entity(f"COMP-{p+1:03}-{k+1}", "component", f"Lumen {p+1:03} {label}") for k,label in enumerate(["Interface", "Gateway", "Index", "Job Queue", "Audit Store"])],
            "baseline_milestone": entity(f"MILESTONE-{p+1:03}-A", "milestone", f"Lumen {p+1:03} baseline launch"),
            "revised_milestone": entity(f"MILESTONE-{p+1:03}-B", "milestone", f"Lumen {p+1:03} revised launch"),
            "domain":domain, "audience":audience, "task":task, "failure":failure,
            "start":start, "baseline_date":(start+timedelta(days=60)).date().isoformat(),
            "revised_date":(start+timedelta(days=67+(p%3)*7)).date().isoformat(),
            "budget":budget, "pilot_users":24+(p%9)*8, "capacity":40+(p%11)*15,
            "delay_days":7+(p%3)*7, "priority":["quality", "delivery predictability", "operator effort", "recoverability"][p%4],
        }
        projects.append(project)

    def name(eid): return entities[eid]["name"]

    for pr in projects:
        p = pr["index"]
        for t, (slug, title, para1, para2) in enumerate(TYPE_SPECS):
            did = f"DOC-{p*20+t+1:05}"
            published = utc(pr["start"] + timedelta(days=t*2))
            refs = []
            edge_rows = []
            fact_rows = []

            def statement(text, source_entity=None, target_entity=None, predicate=None, fact_key=None, value=None):
                sid = f"{did}:S{len(refs)+1:02}"
                anchor = sid.split(":")[1]
                prov = {"document_id":did, "statement_id":sid, "anchor":anchor,
                        "path":f"corpus/documents/{did}.md", "source_quote":text,
                        "recorded_at":published}
                refs.append({"id":sid,"text":text})
                for eid in [source_entity, target_entity]:
                    if eid and prov not in entities[eid]["provenance"]:
                        entities[eid]["provenance"].append(prov)
                if predicate:
                    er = {"id":f"REL-{len(relations)+len(edge_rows)+1:06}", "subject":source_entity,
                          "predicate":predicate, "object":target_entity, "synthetic":True,
                          "valid_from":published,"valid_to":None,"provenance":[prov]}
                    edge_rows.append(er)
                if fact_key:
                    fact_rows.append({"id":f"FACT-{len(facts)+len(fact_rows)+1:06}","entity_id":source_entity,
                                      "key":fact_key,"value":value,"synthetic":True,
                                      "valid_from":published,"provenance":[prov]})
                return sid

            pj, prod, customer = pr["project"],pr["product"],pr["customer"]
            c = pr["components"][t % 5]
            owner = pr["owner"]
            reviewer = pr["reviewer"]
            sponsor = pr["sponsor"]
            if t == 0:
                statement(f"{name(pj)} delivers {name(prod)}.", pj,prod,"DELIVERS")
                statement(f"{name(pj)} is owned by {name(owner)}.",pj,owner,"OWNED_BY")
                statement(f"{name(pj)} is sponsored by {name(sponsor)}.",pj,sponsor,"SPONSORED_BY")
                statement(f"{name(prod)} serves {name(customer)}.",prod,customer,"SERVES")
                statement(f"{name(pj)} belongs to {name(company)}.",pj,company,"BELONGS_TO")
            elif t == 2:
                statement(f"{name(prod)} is supplied by {name(pr['supplier'])}.",prod,pr["supplier"],"SUPPLIED_BY")
                statement(f"{name(pr['supplier'])} supplies {name(c)}.",pr["supplier"],c,"SUPPLIES")
                statement(f"{name(owner)} manages the supplier agreement for {name(pj)}.",owner,pj,"MANAGES_AGREEMENT_FOR")
            elif t == 13:
                statement(f"{name(pj)} is scheduled for {name(pr['baseline_milestone'])}.",pj,pr["baseline_milestone"],"SCHEDULED_FOR")
                statement(f"{name(sponsor)} authorizes the baseline schedule for {name(pj)}.",sponsor,pj,"AUTHORIZES_BASELINE_FOR")
                statement(f"{name(pr['baseline_milestone'])} is planned for {pr['baseline_date']}.",pr["baseline_milestone"],fact_key="planned_launch_date",value=pr["baseline_date"])
            elif t == 16:
                statement(f"{name(pj)} is scheduled for {name(pr['revised_milestone'])}.",pj,pr["revised_milestone"],"SCHEDULED_FOR")
                statement(f"{name(pr['revised_milestone'])} supersedes {name(pr['baseline_milestone'])}.",pr["revised_milestone"],pr["baseline_milestone"],"SUPERSEDES")
                statement(f"{name(pr['revised_milestone'])} is planned for {pr['revised_date']}.",pr["revised_milestone"],fact_key="planned_launch_date",value=pr["revised_date"])
                statement(f"{name(sponsor)} approves the revised schedule for {name(pj)}.",sponsor,pj,"APPROVES_REVISION_FOR")
            else:
                verbs = ["documents", "designs", "sources", "operates", "researches", "specifies", "implements", "reviews access for", "reviews accessibility for", "tests", "observes pilot use of", "investigates incidents for", "proposes changes to", "schedules", "reviews risks for", "reviews budget for", "approves", "communicates changes for", "supports", "maintains"]
                actor = reviewer if t in [7,8,9,10,11,14] else sponsor if t in [15,17] else owner
                statement(f"{name(actor)} {verbs[t]} {name(pj)}.",actor,pj,slug.upper()+"_RESPONSIBILITY")
                statement(f"{name(prod)} depends on {name(c)} for the {title.lower()} scope.",prod,c,"DEPENDS_ON")
                statement(f"{name(customer)} participates in the {title.lower()} for {name(pj)}.",customer,pj,slug.upper()+"_PARTICIPANT")
            statement(f"{name(pr['team'])} operates {name(c)}.",pr["team"],c,"OPERATES")
            statement(f"{name(c)} is part of {name(prod)}.",c,prod,"PART_OF")
            if t == 3:
                statement(f"{name(prod)} has a planning capacity of {pr['capacity']} requests per minute; this is a target, not a benchmark result.",prod,fact_key="planned_requests_per_minute",value=pr["capacity"])
            if t == 10:
                statement(f"{name(customer)} enrolled {pr['pilot_users']} synthetic users in the pilot.",customer,fact_key="pilot_user_count",value=pr["pilot_users"])
            if t == 15:
                statement(f"{name(pj)} has an approved planning budget of {pr['budget']} fictional USD.",pj,fact_key="approved_budget_usd",value=pr["budget"])
            if t == 11:
                statement(f"The recorded trigger for {name(pj)} was {pr['failure']} during the synthetic pilot.",pj,fact_key="incident_trigger",value=pr["failure"])

            reference_id = f"DOC-{p*20+1:05}"
            prior = f"DOC-{p*20+t:05}" if t else None
            effective_note = "This record contains a proposal; the baseline remains authoritative." if t==12 else "This record supersedes the baseline schedule recorded in DOC-%05d."%(p*20+14) if t==16 else "This record must be read using its recorded publication time."
            paragraphs = [
                f"{name(pj)} develops {name(prod)} for {pr['audience']} at {name(customer)}. The workflow helps users {pr['task']}. This document covers the {title.lower()} and gives the team a stable reference for decisions about {pr['domain']}. The current review priority is {pr['priority']}; that priority is a stated preference, not a numeric performance claim.",
                para1,
                para2,
                f"For this project, the team will inspect {name(c)} and retain the source records behind each material finding. {effective_note} Follow-up decisions should identify their assumptions, the person responsible, and the observable condition that would change the recommendation. The document is intentionally part of a fictional evaluation corpus and contains no private customer data.",
            ]
            body = f"# {title}: {name(pj)}\n\nSYNTHETIC DATA — fictional portfolio and evaluation material.\n\nDocument ID: {did}\nPublished UTC: {published}\nProject ID: {pj}\nDocument type: {slug}\nWorkspace: aster-vale-demo\nSource domain: astervale.example\n\n## Context and decision record\n\n" + "\n\n".join(paragraphs)
            body += "\n\n## Evidence statements\n\n" + "\n\n".join(f"### {r['id'].split(':')[1]}\n\n{r['text']}" for r in refs)
            body += f"\n\n## Related records\n\nCharter: {reference_id}."
            if prior: body += f" Previous checkpoint: {prior}."
            body += "\n\n## Use boundary\n\nThese records support retrieval and scenario exercises. Simulated outcomes must remain separate from this source corpus. Gold evaluation answers are withheld from ingestion.\n"
            file = docs_dir / f"{did}.md"
            file.write_text(body,encoding="utf-8")
            row = {"document_id":did,"path":f"corpus/documents/{did}.md","project_id":pj,
                   "type":slug,"title":f"{title}: {name(pj)}","published_at":published,
                   "synthetic":True,"sha256":digest(file),"word_count":len(body.split()),
                   "statement_ids":[x["id"] for x in refs],"supersedes":[f"DOC-{p*20+14:05}"] if t==16 else []}
            docs.append(row); by_doc[did]={"manifest":row,"statements":refs}
            relations.extend(edge_rows); facts.extend(fact_rows)

    # Close the temporal validity of baseline schedule assertions once a revision takes effect.
    for r in relations:
        if r["predicate"]=="SCHEDULED_FOR" and r["object"].endswith("-A"):
            p=int(r["subject"].split("-")[1])-1
            r["valid_to"]=utc(projects[p]["start"]+timedelta(days=32))
    for f in facts:
        if f["key"]=="planned_launch_date" and f["entity_id"].endswith("-A"):
            p=int(f["entity_id"].split("-")[1])-1
            f["valid_to"]=utc(projects[p]["start"]+timedelta(days=32))

    write_jsonl(root/"reference_graph/entities.jsonl",entities.values())
    write_jsonl(root/"reference_graph/relations.jsonl",relations)
    write_jsonl(root/"reference_graph/facts.jsonl",facts)
    write_jsonl(root/"manifests/documents.jsonl",docs)
    for label,n in [("smoke",20),("medium",200),("stress",2000)]:
        write_json(root/f"manifests/{label}.json",{"schema":SCHEMA,"profile":label,"synthetic":True,
            "ingestion_mode":"raw_documents","documents":docs[:n],"exclude_directories":["evaluation_private","reference_graph","personas","scenarios"],
            "notes":"Paths reference the same corpus files. Do not duplicate documents between profiles. Root-relative paths resolve from dataset/."})

    personas=[]
    for i,eid in enumerate(people):
        e=entities[eid]
        personas.append({"id":f"PERSONA-{i+1:03}","entity_id":eid,"name":e["name"],"synthetic":True,
            "role":["delivery owner","project sponsor","quality reviewer"][i%3],
            "goal":["complete a useful pilot with documented limitations","keep commitments consistent with evidence","protect acceptance quality and recoverability"][i%3],
            "priority_weights":{"quality":1+(i%5),"time":1+((i+2)%5),"cost":1+((i+4)%5)},
            "communication_style":["brief and evidence-oriented","asks clarifying questions","compares alternatives before deciding"][i%3],
            "risk_tolerance":["low","moderate","high"][i%3],
            "assumption_notice":"Behavioral traits are authored simulation assumptions, not inferred facts about a real person.",
            "source_evidence":e["provenance"][:3]})
    write_jsonl(root/"personas/synthetic_personas.jsonl",personas)

    queries=[]; gold=[]
    for pr in projects[:40]:
        p=pr["index"]; base=p*20
        cases=[
            ("single_hop",f"Who owns {name(pr['project'])}?",name(pr["owner"]),[f"DOC-{base+1:05}:S02"],None),
            ("multi_hop",f"Which supplier supplies the product delivered by {name(pr['project'])}?",name(pr["supplier"]),[f"DOC-{base+1:05}:S01",f"DOC-{base+3:05}:S01"],None),
            ("temporal",f"As of {(pr['start']+timedelta(days=28)).date().isoformat()}, what was the planned launch date for {name(pr['project'])}?",pr["baseline_date"],[f"DOC-{base+14:05}:S01",f"DOC-{base+14:05}:S03"],utc(pr["start"]+timedelta(days=28))),
            ("temporal",f"As of {(pr['start']+timedelta(days=36)).date().isoformat()}, what was the planned launch date for {name(pr['project'])} and which milestone did it supersede?",{"planned_date":pr["revised_date"],"superseded_milestone":name(pr["baseline_milestone"])},[f"DOC-{base+17:05}:S01",f"DOC-{base+17:05}:S02",f"DOC-{base+17:05}:S03"],utc(pr["start"]+timedelta(days=36))),
            ("unanswerable",f"What was the actual production launch completion timestamp for {name(pr['product'])}?",None,[],None),
        ]
        for typ,q,a,evidence,asof in cases:
            qid=f"EVAL-{len(queries)+1:04}"
            queries.append({"id":qid,"question":q,"category":typ,"as_of":asof,"synthetic":True})
            gold.append({"id":qid,"expected_answer":a,"gold_evidence":evidence,"answerable":typ!="unanswerable",
                         "grading_notes":"Accept semantic equivalence with supporting citations." if a else "Must state that actual completion is not recorded; planned dates do not prove launch completion.",
                         "usage":"EVALUATION ONLY. Never ingest, train, embed, or supply as retrieval context."})
    write_jsonl(root/"evaluation_private/questions.jsonl",queries)
    write_jsonl(root/"evaluation_private/gold_answers.jsonl",gold)
    (root/"evaluation_private/DO_NOT_INGEST.txt").write_text("Evaluation-only holdout. Do not ingest or train on these questions or gold answers. Run them after indexing the raw corpus.\n",encoding="utf-8")

    scenarios=[
        ("release-delay","A required dependency is delayed by fourteen days after the latest release decision.","How might stakeholders revise scope, communication, and readiness decisions?"),
        ("supplier-interruption","The primary supplier cannot deliver the next planned update; an alternate supplier is proposed.","Which stakeholders request evidence, alternative sourcing, or schedule changes?"),
        ("capacity-pressure","The pilot request volume becomes twice the planning capacity while the budget stays fixed.","How might the team balance queue controls, feature scope, and customer expectations?"),
        ("budget-reduction","The next planning budget is reduced by twenty percent after pilot feedback is published.","Which priorities are retained, deferred, or challenged by the stakeholders?")]
    for s,(slug,intervention,question) in enumerate(scenarios):
        selected_projects=projects[s*4:s*4+4]
        selected_ids=[f"DOC-{pr['index']*20+t+1:05}" for pr in selected_projects for t in [0,2,3,10,13,16,18]]
        actor_ids=sorted({x for pr in selected_projects for x in [pr["owner"],pr["sponsor"],pr["reviewer"]]})
        sid=f"SCENARIO-{s+1:02}"
        manifest={"schema":SCHEMA,"id":sid,"name":slug,"synthetic":True,"canonical_format":True,
            "engine_native_format":False,"engine_integration_status":"Not executed or validated against MiroFish.",
            "question":question,"intervention":{"text":intervention,"status":"COUNTERFACTUAL ASSUMPTION, not source fact",
                "applies_to_project_ids":[pr["project"] for pr in selected_projects],
                "scope_note":"Apply the stated intervention separately to each selected project, then explore shared portfolio coordination."},
            "source_documents":selected_ids,"actor_entity_ids":actor_ids,"reference_graph":"reference_graph/",
            "recommended_first_run":{"actors":12,"rounds":5,"max_concurrent_llm_requests":2,"random_seed":seed+s,
                "notes":"These are app-side budgets, not a claim about upstream MiroFish parameter names."},
            "expected_outputs":["action log","stakeholder summaries","assumption list","source evidence references","run configuration"],
            "evaluation_boundary":"Explore hypotheses. Outcomes are not validated forecasts or factual additions to the source corpus."}
        write_json(root/f"scenarios/{sid}_{slug}/scenario.json",manifest)
        lines=[f"SYNTHETIC CANONICAL SIMULATION SEED: {sid}","Not a native MiroFish API payload. Convert through a version-pinned adapter.",f"Question: {question}",f"COUNTERFACTUAL INTERVENTION: {intervention}","Scope: Apply separately to each selected project; the shared company coordinates the portfolio response.","", "ACTORS"]
        lines.extend(f"{eid}: {name(eid)}" for eid in actor_ids)
        lines+= ["", "SOURCE EVIDENCE (facts from fictional source records; preserve IDs)"]
        for did in selected_ids:
            d=by_doc[did]
            lines.append(f"\nDOCUMENT {did} | {d['manifest']['published_at']} | {d['manifest']['path']}")
            lines.extend(f"[{r['id']}] {r['text']}" for r in d["statements"])
        lines+= ["", "BOUNDARY: Agent actions, preferences, and outcomes generated during simulation are simulated. Keep them separate from source assertions."]
        seed_path=root/f"scenarios/{sid}_{slug}/canonical_seed.txt"
        seed_path.write_text("\n".join(lines)+"\n",encoding="utf-8")

    readme="""# Aster Vale synthetic knowledge and simulation corpus

This is fictional, authored test data for a native macOS knowledge app. No records describe actual people, companies, customers, or news. All domains use `.example`. Behavioral traits and interventions are simulation assumptions. Currency values are fictional planning amounts.

## Contents

- `corpus/documents/`: 2,000 Markdown documents across 100 related projects, with 20 document types, dated records, evidence statements, and baseline/revised schedules.
- `manifests/`: document hashes and profiles referencing the same files: smoke 20, medium 200, stress 2,000.
- `reference_graph/`: canonical ground-truth entities, relationships, and scalar facts. Every assertion has a source quotation and statement identifier. This is a benchmark/reference graph, not automatically the app's extracted graph.
- `personas/`: 240 explicitly synthetic stakeholder profiles with evidence-linked roles and authored behavioral assumptions.
- `scenarios/`: four counterfactual scenario manifests and text seed bundles, each selecting evidence and twelve actors.
- `evaluation_private/`: 200 held-out questions and separate gold answers. Evaluation only, never ingestion or training data.
- `generate_dataset.py`, `validate_dataset.py`: deterministic standard-library tools.
- Optional `rich_fixtures/` contains alternate-format copies of selected source documents and its own manifest. These copies support PDF/DOCX/image/OCR tests; they are outside the default raw-document profiles. Preserve their `variant_of` source mapping and avoid counting a format copy as independent evidence.

## Import order

1. Import only the document paths in `manifests/smoke.json`. This indexes the twenty documents for one project.
2. Ask about its owner, supplier, and launch plan at different dates. Verify source clicks reach the named statements.
3. Expand to `medium.json`, then `stress.json`. Deduplicate by document ID/hash; the profiles reference overlapping documents and contain no duplicated physical copies.
4. Derive the app's graph from the raw documents. Compare it with `reference_graph/` only in evaluation mode. Loading the reference graph is a separate explicit demo mode and must not be reported as successful graph extraction.
5. Run questions after indexing; a separate evaluator reads gold answers. Keep both outside all ingestion roots.
6. For simulation, select a scenario and export its evidence, actor candidates, and counterfactual intervention through the MiroFish adapter.

## Simulation adapter boundary

The JSON and seed files are a canonical app dataset, **not** a documented native MiroFish import format. No MiroFish engine was executed to produce this corpus. Inspect and pin the actual engine, convert canonical records into its verified text/profile/configuration inputs, and record native ID mappings. The seed TXT can be used as source material where the selected engine accepts text; it does not configure a complete simulation by itself.

MiroFish integration must preserve `document_id`, `statement_id`, exact `source_quote`, timestamps, and actor mappings. Keep canonical wiki assertions separate from simulation memory and generated outcomes. Never load gold evaluation answers into an engine context. A large corpus should be retrieved and sampled; do not put all documents into one model prompt or instantiate every entity as an actor.

Scenario budgets are recommendations for the application's scheduler, not asserted upstream API fields. Run a small end-to-end experiment before increasing rounds or actors. Pin model and engine versions, record generation settings and seed, and retain incomplete results honestly. Simulation output is exploratory and is not a calibrated forecast.

## Temporal semantics

Publication timestamps are UTC. Each project has an authoritative baseline schedule at day 26 and a revised decision at day 32. The later document explicitly supersedes the earlier schedule. A planned launch date is never evidence of actual production launch. `valid_to` marks superseded graph assertions. Some proposal documents deliberately discuss changes without authorizing them.

## Regenerate and validate

From this directory:

```bash
python3 generate_dataset.py --output . --seed 731902
python3 validate_dataset.py --root .
```

Generation is deterministic for the same script and seed. It replaces generated files with the same names; it does not delete unrelated content. The validator checks counts, document hashes, entity references, exact source quotations, statement anchors, profile membership, scenario references, and held-out answer evidence.

## Dataset usage

This dataset is for ingestion, retrieval, graph extraction, and simulation integration exercises. It is not a training dataset and contains no measured model benchmarks. Document narratives vary across twenty workflow types and one hundred project configurations, while using repeated organizational conventions deliberately. It is suitable for functional and scale testing; it is not representative evidence of real enterprise performance.
"""
    (root/"README.md").write_text(readme,encoding="utf-8")
    # Enumerate only this generator's outputs; unrelated files and optional rich fixtures
    # must not change the deterministic canonical corpus manifest.
    generated_files=[root/d["path"] for d in docs]
    for dirname in ["reference_graph","manifests","personas","scenarios","evaluation_private"]:
        generated_files.extend(p for p in (root/dirname).rglob("*") if p.is_file())
    generated_files.extend(root/name for name in ["README.md","generate_dataset.py","validate_dataset.py"] if (root/name).exists())
    manifest={"schema":SCHEMA,"seed":seed,"synthetic":True,"generated_at":"2026-11-09T00:00:00Z",
              "generated_at_note":"Fixed reproducibility metadata; not a source-event timestamp.",
              "counts":{"documents":len(docs),"entities":len(entities),"relations":len(relations),"facts":len(facts),"personas":len(personas),"evaluation_questions":len(queries),"scenarios":4},
              "word_count":{"min":min(d["word_count"] for d in docs),"max":max(d["word_count"] for d in docs),"total":sum(d["word_count"] for d in docs)},
              "files":[{"path":str(p.relative_to(root)),"sha256":digest(p),"bytes":p.stat().st_size} for p in sorted(generated_files)]}
    write_json(root/"dataset_manifest.json",manifest)
    print(json.dumps({"root":str(root),"counts":manifest["counts"],"word_count":manifest["word_count"]},indent=2))

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--output",type=Path,default=Path(__file__).parent);ap.add_argument("--seed",type=int,default=SEED)
    args=ap.parse_args();generate(args.output.resolve(),args.seed)
