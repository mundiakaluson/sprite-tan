import csv
rows=list(csv.DictReader(open('cards_before_rarity.csv')))
f=list(rows[0].keys()); 
if 'rarity' not in f: f.insert(f.index('cat')+1,'rarity')
def score(r): return int(r['slots'])*10+float(r['cd'])*0.8+float(r['risk'])*0.3-float(r['succ'])*0.1
tit=[r for r in rows if r['cat']=='TITAN']
tit.sort(key=lambda r:-(int(r['slots'])*10+float(r['cd'])))
for i,r in enumerate(tit): r['rarity']='LEGEND' if i<10 else 'EPIC'
rest=[r for r in rows if r['cat']!='TITAN']
cats={}
for r in rest: cats.setdefault(r['cat'],[]).append(r)
ranked=[]
for c,v in cats.items():
    v.sort(key=lambda r:(-score(r),r['id']))
    for i,r in enumerate(v): ranked.append(((i+0.5)/len(v),r['id'],r))
ranked.sort(key=lambda x:(x[0],x[1]))
cut=[('EPIC',15),('RARE',40),('UNCOMMON',55),('COMMON',65)]
i=0
for t,n in cut:
    for _,_,r in ranked[i:i+n]: r['rarity']=t
    i+=n
assert i==len(rest)
order={r['id']:i for i,r in enumerate(csv.DictReader(open('cards_before_rarity.csv')))}
rows.sort(key=lambda r:order[r['id']])
w=csv.DictWriter(open('cards.csv','w',newline=''),fieldnames=f); w.writeheader(); w.writerows(rows)
from collections import Counter
print(Counter(r['rarity'] for r in rows))
for c in ['SHOT','DEFEND','KEEPER','SUPPORT']:
    print(c,Counter(r['rarity'] for r in rows if r['cat']==c))
print([ (r['name'],r['rarity']) for r in rows if r['cat']=='SHOT'][:12])
print([ (r['name'],r['rarity']) for r in rows if r['cat']=='TITAN'][:6])
