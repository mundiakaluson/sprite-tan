import csv
# Outfield: PAC SHO PAS DRI DEF PHY   Keeper: REF HAN POS   (first = main stat, second = minor)
S = {}
def a(ids, v):
    for i in ids.split(): S[i] = v
# SHOTS
a("SH01 SH14 SH16 SH18 SH23 SH24 SH25 SH28 SH26", "SHO")
a("SH02 SH07 SH22", "SHO+PHY")
a("SH03 SH04 SH17 SH19 SH20 SH21 SH27", "SHO+PAS")
a("SH05 SH29", "SHO+DRI"); a("SH06", "SHO+PHY")
a("SH08 SH09 SH13 SH15 SH30", "SHO+DRI")
a("SH10 SH11 SH12", "SHO+PHY")
S["SH28"]="SHO"; S["SH26"]="SHO+DRI"
# PASSES
a("PS01 PS02 PS03 PS04 PS05 PS06 PS09 PS10 PS12 PS13 PS14 PS15 PS16 PS17 PS18 PS23 PS24 PS25 PS22", "PAS")
a("PS07 PS08 PS11 PS19 PS20 PS21", "PAS+SHO")
a("PS18", "PAS+PHY"); a("PS24", "PAS+PHY")
# DRIBBLES
a("DR01 DR02 DR03 DR04 DR05 DR06 DR07 DR08 DR09 DR10 DR11 DR14 DR15 DR16 DR18 DR19 DR20 DR21 DR22 DR23 DR26 DR27 DR28 DR29 DR30", "DRI")
a("DR12 DR13", "PHY+DRI"); a("DR17 DR24 DR25", "PAC+DRI")
S["DR01"]="DRI+PAC"; S["DR10"]="DRI+SHO"; S["DR19"]="DRI+PAS"
# DEFENDING
a("DF01 DF03 DF10 DF19 DF25 DF26 DF33 DF34 DF28", "DEF")
a("DF02 DF13 DF15 DF24 DF35 DF06 DF12 DF08", "DEF+PHY")
a("DF04 DF05 DF17 DF18 DF20 DF22 DF23 DF27 DF29 DF30 DF31 DF09 DF11", "DEF")
a("DF07 DF21", "DEF+PAC"); a("DF14 DF16 DF32", "DEF+PHY")
S["DF16"]="PHY+DEF"; S["DF02"]="DEF+PAC"; S["DF11"]="DEF+PAC"; S["DF29"]="DEF+PAC"
# KEEPER
a("GK01 GK11 GK13 GK15 GK19 GK22 GK23", "POS")
a("GK02 GK09 GK10 GK12 GK14 GK20 GK24", "REF"); S["GK12"]="REF+POS"; S["GK14"]="REF"
a("GK03 GK04 GK05 GK08 GK21 GK25", "HAN"); S["GK03"]="HAN+POS"; S["GK05"]="HAN+POS"; S["GK21"]="HAN+POS"
a("GK06", "POS+PAC")
a("GK07 GK17", "PAS"); a("GK16 GK18", "PAS+PHY")
# TITAN
a("TT01", "PAC+DRI"); a("TT02", "SHO+PHY"); a("TT04", "DRI+PAS"); a("TT05", "SHO+DRI")
a("TT07", "SHO+PAC"); a("TT08", "DEF+PHY"); a("TT09", "PAS"); a("TT10", "SHO+PAS")
a("TT11", "SHO+PHY"); a("TT12", "REF+HAN"); a("TT13", "DEF+PHY"); a("TT14", "PAC+DRI")
a("TT15", "SHO+PHY"); a("TT16", "PAS+DRI"); a("TT17", "DEF+PHY"); a("TT18", "DRI+DEF")
a("TT20", "DEF+PAC"); a("TT21", "SHO+PHY"); a("TT22", "SHO+PAS")
rows = list(csv.DictReader(open('cards_backup.csv')))
f = list(rows[0].keys())
i = f.index('kind')+1 if 'stats' not in f else f.index('stats')
if 'stats' not in f: f.insert(i,'stats')
miss=[]
for r in rows:
    if r['kind']=='BUFF' or r['cat']=='SUPPORT' or r['id'] in ("TT03","TT06","TT19","TT23","TT24","TT25"):
        r['stats']='' 
    else:
        r['stats']=S.get(r['id'],'')
        if not r['stats']: miss.append(r['id'])
w=csv.DictWriter(open('cards.csv','w',newline=''),fieldnames=f); w.writeheader(); w.writerows(rows)
print('missing',miss, 'rows',len(rows))
