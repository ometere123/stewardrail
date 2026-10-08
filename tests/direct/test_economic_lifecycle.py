import hashlib,json
from pathlib import Path
import pytest
from tests.direct.genvm_stub import Runtime,load,deploy
ROOT=Path(__file__).resolve().parents[2]
A='0x'+'1'*40;B='0x'+'2'*40;AGENT='0x'+'3'*40;ISSUER='0x'+'4'*40;PAYEE='0x'+'5'*40;CHALLENGER='0x'+'6'*40
CHARTER='0x'+'a'*40;REGISTRY='0x'+'b'*40;COURT='0x'+'c'*40;GUARD='0x'+'d'*40;VAULT='0x'+'e'*40
URI='https://issuer.example/invoice/1'

def mandate(tight=False, consequence="refuse", recipient_limit=None):
    rolling_amount = 1000 if tight else 5000
    deterministic={'max_per_spend':1000,'rolling_limit':{'amount':rolling_amount,'seconds':86400},'category_allowlist':['ops'],'recipient_denylist':[]}
    if recipient_limit is not None: deterministic['recipient_rolling']={'amount':recipient_limit,'seconds':86400}
    return {
      'name':'Shared Treasury','deterministic':deterministic,
      'semantic_rules':[{'id':'purpose','question':'Does the authenticated evidence show this spend serves the shared mandate?','when':{'type':'amount_gte','value':100},'evidence_roles':['invoice'],'consequence':consequence}],
      'issuers':[{'address':ISSUER,'role':'invoice','origins':['https://issuer.example']}],
      'appeal':{'window_seconds':100,'bond':0},
    }

def setup_stack(tight=False, consequence="refuse"):
    rt=Runtime(); rt.sender=A
    mods={n:load(str(ROOT/'contracts'/f'{n}.py'),rt) for n in ['steward_charter','evidence_registry','steward_court','steward_guard','steward_vault']}
    m=json.dumps(mandate(tight, consequence))
    deploy(rt,mods['steward_charter'],'StewardCharter',CHARTER,json.dumps([A,B]),2,AGENT,m,sender=A)
    deploy(rt,mods['evidence_registry'],'EvidenceRegistry',REGISTRY,sender=A)
    deploy(rt,mods['steward_court'],'StewardCourt',COURT,CHARTER,REGISTRY,sender=A)
    deploy(rt,mods['steward_guard'],'StewardGuard',GUARD,CHARTER,REGISTRY,COURT,sender=A)
    deploy(rt,mods['steward_vault'],'StewardVault',VAULT,CHARTER,GUARD,COURT,sender=A)
    rt.call(CHARTER,'approve_mandate',m,sender=A);rt.call(CHARTER,'approve_mandate',m,sender=B)
    return rt

def attest(rt,body=b'valid invoice'):
    digest=hashlib.sha256(body).hexdigest();rt.web[URI]=body
    rt.call(REGISTRY,'attest',CHARTER,'invoice',URI,digest,sender=ISSUER)
    return digest

def create_semantic(rt,digest):
    rt.call(GUARD,'request_spend',PAYEE,200,'ops',sender=AGENT)
    rt.call(GUARD,'attach_evidence',0,ISSUER,'invoice',URI,digest,sender=AGENT)

def test_threshold_mandate_and_historical_issuer_authentication():
    rt=setup_stack(); cur=json.loads(rt.call(CHARTER,'current',sender=A));assert cur['version']==1
    digest=attest(rt)
    # Attestation happened after requested_at? create spend after attestation so it is historical at request.
    rt.call(GUARD,'request_spend',PAYEE,200,'ops',sender=AGENT)
    rt.call(GUARD,'attach_evidence',0,ISSUER,'invoice',URI,digest,sender=AGENT)
    with pytest.raises(Exception): rt.call(GUARD,'attach_evidence',0,B,'invoice',URI,digest,sender=AGENT)

def test_allow_then_appeal_reverses_to_refuse_and_vault_cannot_pay():
    rt=setup_stack();digest=attest(rt);create_semantic(rt,digest)
    rt.model=lambda p:{'verdict':'allow','confidence':95,'reason':'evidence fits'}
    rt.call(GUARD,'adjudicate',0,sender=A); assert rt.flush_finalized()==1
    case=json.loads(rt.call(COURT,'case',GUARD,0,sender=A)); assert case['primary']=='allow'
    rt.balances[PAYEE]=100
    rt.model=lambda p:{'verdict':'refuse','confidence':92,'reason':'appeal identifies conflict'}
    rt.call(COURT,'appeal',GUARD,0,VAULT,'frozen rule was misapplied','[]',sender=PAYEE)
    rt.flush_finalized()
    case=json.loads(rt.call(COURT,'case',GUARD,0,sender=A));assert case['effective']=='refuse' and case['effective'] != case['primary']
    rt.balances[A]=1000;rt.call(VAULT,'fund',sender=A,value=500)
    with pytest.raises(Exception,match='refuses payment'):rt.call(VAULT,'pay',0,sender=A)
    assert rt.balances[PAYEE]==100

def test_refuse_then_appeal_reverses_to_allow_and_pays_once():
    rt=setup_stack();digest=attest(rt);create_semantic(rt,digest)
    rt.model=lambda p:{'verdict':'refuse','confidence':95,'reason':'initial ambiguity'}
    rt.call(GUARD,'adjudicate',0,sender=A);rt.flush_finalized()
    rt.balances[PAYEE]=100
    rt.model=lambda p:{'verdict':'allow','confidence':95,'reason':'appeal resolves ambiguity'}
    rt.call(COURT,'appeal',GUARD,0,VAULT,'read the authenticated invoice in context','[]',sender=PAYEE)
    rt.flush_finalized()
    terminal=json.loads(rt.call(VAULT,'payment',0,sender=A))['terminal'];assert terminal['decision']=='allow'
    rt.balances[A]=1000;rt.call(VAULT,'fund',sender=A,value=500)
    before=rt.balances.get(PAYEE,0);rt.call(VAULT,'pay',0,sender=A);assert rt.balances[PAYEE]-before==200
    with pytest.raises(Exception,match='already paid'):rt.call(VAULT,'pay',0,sender=A)

def test_unappealed_primary_does_not_reach_vault_until_court_closes_after_window():
    rt=setup_stack();digest=attest(rt);create_semantic(rt,digest);rt.model=lambda p:{'verdict':'allow','confidence':95,'reason':'ok'}
    rt.call(GUARD,'adjudicate',0,sender=A);rt.flush_finalized()
    assert json.loads(rt.call(VAULT,'payment',0,sender=A))['terminal'] is None
    with pytest.raises(Exception,match='has not elapsed'):rt.call(COURT,'close_unappealed',GUARD,0,VAULT,sender=A)
    rt.now+=101;rt.call(COURT,'close_unappealed',GUARD,0,VAULT,sender=A);rt.flush_finalized()
    assert json.loads(rt.call(VAULT,'payment',0,sender=A))['terminal']['decision']=='allow'

def test_digest_mismatch_fails_closed_at_jury():
    rt=setup_stack();digest=attest(rt);create_semantic(rt,digest);rt.web[URI]=b'changed after attestation';rt.model=lambda p:{'verdict':'allow','confidence':100,'reason':'ignore hash'}
    rt.call(GUARD,'adjudicate',0,sender=A);rt.flush_finalized();case=json.loads(rt.call(COURT,'case',GUARD,0,sender=A));assert case['primary']=='refuse'

def test_terminal_refusal_is_removed_from_guard_exposure():
    rt=setup_stack();digest=attest(rt);create_semantic(rt,digest)
    rt.model=lambda p:{'verdict':'allow','confidence':95,'reason':'ok'}
    rt.call(GUARD,'adjudicate',0,sender=A);rt.flush_finalized()
    rt.balances[PAYEE]=100
    rt.model=lambda p:{'verdict':'refuse','confidence':95,'reason':'reversed'}
    rt.call(COURT,'appeal',GUARD,0,VAULT,'conflicting evidence','[]',sender=PAYEE);rt.flush_finalized()
    spend=json.loads(rt.call(GUARD,'get_spend',0,sender=A))
    assert spend['state']=='allow' and spend['terminal_state']=='refuse'
    preview=json.loads(rt.call(GUARD,'preview_spend',PAYEE,200,'ops',sender=A))
    assert preview['state']=='held'

def test_terminal_allow_consumes_single_use_evidence():
    rt=setup_stack();digest=attest(rt);create_semantic(rt,digest)
    rt.model=lambda p:{'verdict':'refuse','confidence':95,'reason':'initial ambiguity'}
    rt.call(GUARD,'adjudicate',0,sender=A);rt.flush_finalized();rt.balances[PAYEE]=100
    rt.model=lambda p:{'verdict':'allow','confidence':95,'reason':'appeal resolves'}
    rt.call(COURT,'appeal',GUARD,0,VAULT,'authenticated invoice','[]',sender=PAYEE);rt.flush_finalized()
    rt.call(GUARD,'request_spend',PAYEE,200,'ops',sender=AGENT)
    rt.call(GUARD,'attach_evidence',1,ISSUER,'invoice',URI,digest,sender=AGENT)
    rt.model=lambda p:{'verdict':'allow','confidence':95,'reason':'reuse'}
    rt.call(GUARD,'adjudicate',1,sender=A);rt.flush_finalized()
    rt.now+=101
    rt.call(COURT,'close_unappealed',GUARD,1,VAULT,sender=A);rt.flush_finalized()
    spend=json.loads(rt.call(GUARD,'get_spend',1,sender=A))
    assert spend['terminal_semantic']=='allow'
    assert spend['terminal_economic']=='refuse'
    assert 'single-use evidence already consumed' in spend['terminal_reason']
    assert json.loads(rt.call(VAULT,'payment',1,sender=A))['terminal']['decision']=='refuse'
    with pytest.raises(Exception,match='terminal decision refuses payment'):
        rt.call(VAULT,'pay',1,sender=A)

def test_direct_court_to_vault_bypass_is_rejected():
    rt=setup_stack()
    with pytest.raises(Exception,match='only the bound guard'):
        rt.call(VAULT,'record_terminal',GUARD,0,'allow',200,PAYEE,sender=COURT)
    with pytest.raises(Exception,match='only the bound guard'):
        rt.call(VAULT,'record_terminal',GUARD,0,'allow',200,PAYEE,sender=A)

def test_semantic_refuse_reserves_capacity_until_terminal_release():
    rt=setup_stack(tight=True); digest=attest(rt)
    rt.call(GUARD,'request_spend',PAYEE,600,'ops',sender=AGENT)
    rt.call(GUARD,'attach_evidence',0,ISSUER,'invoice',URI,digest,sender=AGENT)
    rt.model=lambda p:{'verdict':'refuse','confidence':95,'reason':'not satisfied'}
    rt.call(GUARD,'adjudicate',0,sender=A); rt.flush_finalized()
    rt.call(GUARD,'request_spend',PAYEE,600,'ops',sender=AGENT)
    second=json.loads(rt.call(GUARD,'get_spend',1,sender=A))
    assert second['state']=='refuse' and 'rolling authorization exposure' in second['reason']
    rt.now+=101
    rt.call(COURT,'close_unappealed',GUARD,0,VAULT,sender=A); rt.flush_finalized()
    rt.call(GUARD,'request_spend',PAYEE,600,'ops',sender=AGENT)
    released=json.loads(rt.call(GUARD,'get_spend',2,sender=A))
    assert released['state']=='held'

def test_terminal_reconciliation_redelivers_idempotently():
    rt=setup_stack(); digest=attest(rt); create_semantic(rt,digest)
    rt.model=lambda p:{'verdict':'allow','confidence':95,'reason':'ok'}
    rt.call(GUARD,'adjudicate',0,sender=A); rt.flush_finalized(); rt.now+=101
    rt.call(COURT,'close_unappealed',GUARD,0,VAULT,sender=A); rt.flush_finalized()
    first=json.loads(rt.call(VAULT,'payment',0,sender=A))['terminal']
    rt.call(COURT,'reconcile_terminal',GUARD,0,VAULT,sender=A); rt.flush_finalized()
    second=json.loads(rt.call(VAULT,'payment',0,sender=A))['terminal']
    assert first==second

def test_freeze_requires_threshold_unfreeze_and_replay_fails():
    rt=setup_stack(consequence="freeze"); digest=attest(rt); create_semantic(rt,digest)
    rt.model=lambda p:{'verdict':'refuse','confidence':95,'reason':'breach'}
    rt.call(GUARD,'adjudicate',0,sender=A); rt.flush_finalized()
    rt.now += 101; rt.call(COURT,'close_unappealed',GUARD,0,VAULT,sender=A); rt.flush_finalized()
    status=json.loads(rt.call(GUARD,'enforcement_status',sender=A)); assert status['agent_frozen'] is True
    with pytest.raises(Exception, match='frozen'):
        rt.call(GUARD,'request_spend',PAYEE,1,'ops',sender=AGENT)
    with pytest.raises(Exception, match='threshold approval'):
        rt.call(GUARD,'unfreeze',sender=A)
    epoch=status['freeze_epoch']; nonce=status['unfreeze_nonce']
    rt.call(CHARTER,'approve_unfreeze',GUARD,epoch,nonce,sender=A)
    with pytest.raises(Exception, match='threshold approval'):
        rt.call(GUARD,'unfreeze',sender=A)
    rt.call(CHARTER,'approve_unfreeze',GUARD,epoch,nonce,sender=B)
    rt.call(GUARD,'unfreeze',sender=A)
    with pytest.raises(Exception, match='threshold approval'):
        rt.call(GUARD,'unfreeze',sender=A)

def test_observe_consequence_records_observed_breach_without_refusal():
    rt=setup_stack(consequence="observe"); digest=attest(rt); create_semantic(rt,digest)
    rt.model=lambda p:{'verdict':'refuse','confidence':95,'reason':'observed mismatch'}
    rt.call(GUARD,'adjudicate',0,sender=A); rt.flush_finalized()
    spend=json.loads(rt.call(GUARD,'get_spend',0,sender=A))
    assert spend['state']=='allow'
    assert spend['enforcement']=='observe'
    assert 'observed breach' in spend['reason']

def test_charter_rejects_unknown_enforcement_consequence():
    rt=setup_stack()
    with pytest.raises(Exception, match='unsupported semantic consequence'):
        rt.call(CHARTER,'approve_mandate',json.dumps(mandate(consequence='owner_override')),sender=A)

def test_recipient_rolling_limit_blocks_split_spend():
    rt=setup_stack()
    proposal=json.dumps(mandate(recipient_limit=500))
    rt.call(CHARTER,'approve_mandate',proposal,sender=A); rt.call(CHARTER,'approve_mandate',proposal,sender=B)
    for _ in range(2): rt.call(GUARD,'request_spend',PAYEE,199,'ops',sender=AGENT)
    rt.call(GUARD,'request_spend',PAYEE,199,'ops',sender=AGENT)
    third=json.loads(rt.call(GUARD,'get_spend',2,sender=A))
    assert third['state']=='refuse' and 'recipient rolling' in third['reason']

def test_revoke_consequence_blocks_unpaid_prior_allow():
    rt=setup_stack(consequence="revoke"); digest=attest(rt)
    create_semantic(rt,digest)
    rt.model=lambda p:{'verdict':'allow','confidence':95,'reason':'first allowed'}
    rt.call(GUARD,'adjudicate',0,sender=A); rt.flush_finalized(); rt.now += 101
    rt.call(COURT,'close_unappealed',GUARD,0,VAULT,sender=A); rt.flush_finalized()
    rt.call(GUARD,'request_spend',PAYEE,200,'ops',sender=AGENT)
    rt.call(GUARD,'attach_evidence',1,ISSUER,'invoice',URI,digest,sender=AGENT)
    rt.model=lambda p:{'verdict':'refuse','confidence':95,'reason':'severe breach'}
    rt.call(GUARD,'adjudicate',1,sender=A); rt.flush_finalized(); rt.now += 101
    rt.call(COURT,'close_unappealed',GUARD,1,VAULT,sender=A); rt.flush_finalized()
    assert json.loads(rt.call(GUARD,'get_spend',0,sender=A))['revoked'] is True
    with pytest.raises(Exception, match='revoked'):
        rt.call(VAULT,'pay',0,sender=A)
