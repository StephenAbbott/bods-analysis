"""Profile the MEIP BODS v0.4 file: statement counts by record type, relationship
interest types and directOrIndirect values, and how many relationships point straight at
the group head (declarationSubject). Input: meip_bods.jsonl from the OECD's BODS zip.
Run: python3 00_bods_profile.py /path/to/meip_bods.jsonl > results/bods_profile.json"""
import json, sys, collections
path = sys.argv[1] if len(sys.argv) > 1 else 'meip_bods.jsonl'
rt = collections.Counter(); it = collections.Counter(); di = collections.Counter(); to_head = n_rel = 0
for line in open(path):
    s = json.loads(line); rt[s['recordType']] += 1
    if s['recordType'] == 'relationship':
        n_rel += 1; d = s['recordDetails']
        ip = d.get('interestedParty'); ip = ip if isinstance(ip, str) else (ip or {}).get('describedByEntityStatement')
        if ip == s.get('declarationSubject'): to_head += 1
        for i in d.get('interests', []):
            it[i.get('type')] += 1; di[i.get('directOrIndirect')] += 1
print(json.dumps({'statements': sum(rt.values()), 'by_record_type': rt, 'interest_types': it,
                  'directOrIndirect': di, 'relationships': n_rel, 'relationships_whose_interested_party_is_the_group_head': to_head}, indent=1))
