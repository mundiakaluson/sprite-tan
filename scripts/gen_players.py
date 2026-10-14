import csv, random
random.seed(7)
TIERS=[("LEGEND",12,(85,93)),("EPIC",33,(79,86)),("RARE",75,(73,80)),("UNCOMMON",90,(66,74)),("COMMON",90,(58,67))]
ROLES=[("GK",30),("CB",52),("LB",18),("RB",18),("CDM",34),("CM",40),("CAM",26),("LW",18),("RW",18),("ST",46)]
assert sum(n for _,n in ROLES)==300
# stat offsets PAC SHO PAS DRI DEF PHY, and rating weights
OFF={"CB":(-6,-26,-8,-18,8,9),"LB":(5,-18,0,-6,3,-1),"RB":(5,-18,0,-6,3,-1),"CDM":(-6,-14,3,-8,8,6),
"CM":(-2,-6,8,2,-4,-2),"CAM":(0,4,9,8,-18,-8),"LW":(8,2,0,9,-24,-10),"RW":(8,2,0,9,-24,-10),"ST":(3,10,-6,2,-30,2)}
W={"CB":(.1,0,.1,0,.5,.3),"LB":(.25,0,.2,.2,.25,.1),"RB":(.25,0,.2,.2,.25,.1),"CDM":(.05,.05,.25,.1,.35,.2),
"CM":(.1,.15,.35,.25,.1,.05),"CAM":(.1,.25,.3,.3,0,.05),"LW":(.25,.2,.15,.3,0,.1),"RW":(.25,.2,.15,.3,0,.1),"ST":(.15,.45,.05,.15,0,.2)}
SEC={"CB":["CDM","LB","RB"],"LB":["LW","CB","CM"],"RB":["RW","CB","CM"],"CDM":["CM","CB"],"CM":["CDM","CAM"],
"CAM":["CM","LW","RW","ST"],"LW":["ST","CAM","RW","LB"],"RW":["ST","CAM","LW","RB"],"ST":["LW","RW","CAM"],"GK":[]}
ALL=["CB","LB","RB","CDM","CM","CAM","LW","RW","ST"]
FN="Aiden Bruno Carlos Dario Emil Felix Gabe Hugo Ivan Jonas Kofi Luka Mateo Nico Omar Pablo Quin Rafa Sami Teo Uriel Viktor Wes Xavi Yuri Zane Abel Idris Kenji Tariq Joao Marek Anton Ruben Soren Tomas Elio Matheus Dani Leo Kai Ravi Amadou Cesar Dimitri Enzo Fabio Gil Hakim Ilya Jamal Kwame Lars Milan Nuno Otto Piero Rey Stefan Tobias Ugo Vlad Yaw Zico".split()
PRE="Kor Val Dra Mor Sen Bel Tor Ven Ash Zan Ric Lev Mar Ond Pel Sav Tal Bor Cal Dur Fen Gor Hal Jar Kes Lom Nar Oro Pav Qui Rok Sul Tev Urs Vol Wen Yar Zol Ald Bra Cor Dov".split()
SUF="vane ito ski ez ov ar ini ka son man dric lo reta baye go mesh adi ran ek ero tuk wa rin do vic sen th ley mann dal ola bou".split()
used=set(); 
def name():
    while True:
        n=f"{random.choice(FN)} {random.choice(PRE)}{random.choice(SUF)}".replace("  "," ")
        if n not in used: used.add(n); return n
def clamp(v,lo=30,hi=99): return max(lo,min(hi,int(round(v))))
# role list per tier: spread roles across tiers proportionally
pool=[]
for r,n in ROLES: pool+= [r]*n
random.shuffle(pool)
# make sure each tier gets a role mix: assign sequentially by shuffled pool
players=[]; idx=0
for tier,n,(lo,hi) in TIERS:
    for _ in range(n):
        role=pool[idx]; idx+=1
        # rating skewed slightly toward tier's lower middle
        R=clamp(lo+(hi-lo)*random.betavariate(1.6,1.8))
        players.append((tier,role,R))
random.shuffle(players)
HAIR=["H01_buzz","H02_crop","H03_sidepart","H04_quiff","H05_curly","H06_afro","H07_braids","H08_long","H09_ponytail","H10_bun"]
HW=[10,18,14,10,10,7,6,8,9,8]
HCOL=["black","darkbrown","brown","auburn","blonde","ginger","grey","white","platinum","blue"]
HCW=[30,25,18,6,10,4,3,1,2,1]
SKIN=[1,2,3,4,5,6]; SW=[14,22,22,18,14,10]
rows=[]
for i,(tier,role,R) in enumerate(players,1):
    pid=f"PL{i:03d}"
    r={"id":pid,"name":name(),"rarity":tier,"role":role}
    sec=[]
    if role!="GK":
        pool_s=SEC[role][:]
        x=random.random()
        if x<0.28: sec.append(random.choice(pool_s))
        if x<0.05: sec.append(random.choice([a for a in ALL if a!=role and a not in sec]))  # utility
        if tier in("EPIC","LEGEND") and random.random()<0.25 and len(sec)<2:
            c=[a for a in pool_s if a not in sec]
            if c: sec.append(random.choice(c))
    r["roles"]="|".join([role]+sec)
    if role=="GK":
        a=[R+random.randint(-4,4) for _ in range(3)]
        d=R-sum(a)/3; a=[clamp(v+d) for v in a]
        r.update(PAC="",SHO="",PAS="",DRI="",DEF="",PHY="",REF=a[0],HAN=a[1],POS=a[2],rating=R)
    else:
        off=OFF[role]; s=[R+o+random.randint(-5,5) for o in off]
        for _ in range(3):
            cur=sum(w*v for w,v in zip(W[role],s)); s=[v+(R-cur) for v in s]
        s=[clamp(v) for v in s]
        rating=clamp(sum(w*v for w,v in zip(W[role],s)))
        r.update(PAC=s[0],SHO=s[1],PAS=s[2],DRI=s[3],DEF=s[4],PHY=s[5],REF="",HAN="",POS="",rating=rating)
    r["skin"]=random.choices(SKIN,SW)[0]
    hs=random.choices(HAIR,HW)[0]; r["hair_style"]=hs
    r["hair_color"]=random.choices(HCOL,HCW)[0]
    r["beard"]=random.choices(["none","stubble","short","full"],[70,12,10,8])[0]
    if hs in("H07_braids","H08_long","H09_ponytail") and random.random()<.15: r["beard"]="none"
    r["glasses"]=random.choices(["none","clear","dark"],[91,4,5])[0]
    r["chain"]=int(random.random()<.12)
    r["headband"]=int(random.random()<.06)
    r["wristband"]=int(random.random()<.15)
    r["tattoo"]=int(random.random()<.15)
    rows.append(r)
rows.sort(key=lambda r:-r["rating"])
F=["id","name","rarity","role","roles","rating","PAC","SHO","PAS","DRI","DEF","PHY","REF","HAN","POS","skin","hair_style","hair_color","beard","glasses","chain","headband","wristband","tattoo"]
with open("players.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=F); w.writeheader(); w.writerows(rows)
from collections import Counter
print(Counter(r["rarity"] for r in rows)); print(Counter(r["role"] for r in rows))
print("multi-role",sum('|' in r["roles"] for r in rows), "rating range",rows[-1]["rating"],rows[0]["rating"])
for t in ("LEGEND","COMMON"):
    print(t,[ (r["name"],r["role"],r["roles"],r["rating"]) for r in rows if r["rarity"]==t][:3])
