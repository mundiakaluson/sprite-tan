import csv
# pitch coords: x 0..100 left->right, y 0..100 own goal -> opponent goal. GK implicit at (50,5).
# slot = (role, style, x, y)   role = fit role (existing 10 roles), style = behaviour tag (shared table)
F = {}
def f(fid,name,family,over,slots,note): F[fid]=dict(name=name,family=family,over=over,slots=slots,note=note)
CB4=[("CB","stopper",37,18),("CB","ball_playing_cb",63,18)]
FB4=[("LB","fullback",15,22),("RB","fullback",85,22)]
f("F01","4-4-2","FOUR_BACK",{"compactness":.6,"directness":.55},
  FB4+CB4+[("LW","wide_mid",12,48),("CM","box_to_box",38,46),("CM","playmaker",62,46),("RW","wide_mid",88,48),("ST","target",40,72),("ST","poacher",60,72)],
  "Balanced, two banks of four. Direct and honest.")
f("F02","4-3-3","FOUR_BACK",{"width":.7,"press":.65,"overlap":.55},
  FB4+CB4+[("CDM","anchor",50,38),("CM","box_to_box",33,50),("CM","playmaker",67,50),("LW","inside_forward",14,74),("RW","inside_forward",86,74),("ST","poacher",50,80)],
  "Wide forwards, high press, one holding mid.")
f("F03","4-2-3-1","FOUR_BACK",{"compactness":.6,"directness":.45},
  FB4+CB4+[("CDM","anchor",38,38),("CDM","deep_playmaker",62,38),("LW","winger",15,62),("CAM","playmaker",50,62),("RW","winger",85,62),("ST","target",50,80)],
  "Double pivot, a creator behind a lone striker.")
f("F04","4-1-4-1","FOUR_BACK",{"line_height":.45,"compactness":.7,"counter":.6},
  FB4+CB4+[("CDM","anchor",50,34),("LW","wide_mid",15,52),("CM","box_to_box",38,52),("CM","box_to_box",62,52),("RW","wide_mid",85,52),("ST","target",50,78)],
  "Compact midfield four in front of a screen. Counter-attacking.")
f("F05","4-3-2-1","FOUR_BACK",{"width":.45,"compactness":.75,"directness":.4},
  FB4+CB4+[("CM","box_to_box",30,42),("CDM","anchor",50,38),("CM","box_to_box",70,42),("CAM","shadow",32,62),("CAM","shadow",68,62),("ST","poacher",50,80)],
  "Narrow Christmas tree. Two shadows feed one striker. Fullbacks give width.")
f("F06","4-1-2-1-2","FOUR_BACK",{"width":.4,"overlap":.7,"directness":.5},
  FB4+CB4+[("CDM","anchor",50,34),("CM","box_to_box",30,46),("CM","box_to_box",70,46),("CAM","playmaker",50,60),("ST","target",40,76),("ST","poacher",60,76)],
  "Narrow diamond. Fullbacks must supply all the width.")
f("F07","3-5-2","THREE_BACK",{"width":.65,"overlap":.7},
  [("CB","stopper",30,18),("CB","sweeper",50,15),("CB","stopper",70,18),("LB","wingback",8,48),("RB","wingback",92,48),("CDM","anchor",50,36),("CM","box_to_box",34,46),("CM","playmaker",66,46),("ST","target",40,74),("ST","poacher",60,74)],
  "Wingbacks supply width, two strikers up top.")
f("F08","3-4-3","THREE_BACK",{"press":.7,"line_height":.6,"risk":.6},
  [("CB","stopper",30,18),("CB","sweeper",50,15),("CB","stopper",70,18),("LB","wingback",10,45),("CM","box_to_box",38,42),("CM","playmaker",62,42),("RB","wingback",90,45),("LW","inside_forward",18,72),("RW","inside_forward",82,72),("ST","poacher",50,80)],
  "All-out attack. Three forwards and wingbacks. Vulnerable on the break.")
f("F09","5-3-2","FIVE_BACK",{"counter":.65},
  [("CB","stopper",28,16),("CB","sweeper",50,14),("CB","stopper",72,16),("LB","wingback",8,34),("RB","wingback",92,34),("CM","box_to_box",30,46),("CDM","anchor",50,42),("CM","box_to_box",70,46),("ST","target",42,70),("ST","poacher",58,70)],
  "Solid back five, quick strike pair.")
f("F10","5-4-1","FIVE_BACK",{"line_height":.25,"press":.2,"compactness":.9,"directness":.7,"counter":.8,"risk":.25},
  [("CB","stopper",28,16),("CB","sweeper",50,14),("CB","stopper",72,16),("LB","wingback",8,32),("RB","wingback",92,32),("LW","wide_mid",15,50),("CM","anchor",38,46),("CM","anchor",62,46),("RW","wide_mid",85,50),("ST","target",50,74)],
  "Low block. Concede space, hit on the counter.")
# family defaults (base class). All 0..1.
FAM={"FOUR_BACK":dict(line_height=.5,width=.6,compactness=.55,press=.5,overlap=.5,directness=.5,counter=.5,risk=.5),
"THREE_BACK":dict(line_height=.5,width=.65,compactness=.55,press=.55,overlap=.6,directness=.5,counter=.5,risk=.5),
"FIVE_BACK":dict(line_height=.35,width=.6,compactness=.7,press=.35,overlap=.35,directness=.6,counter=.65,risk=.4)}
P=["line_height","width","compactness","press","overlap","directness","counter","risk"]
with open("formation_families.csv","w",newline="") as fh:
    w=csv.writer(fh); w.writerow(["family"]+P)
    for k,v in FAM.items(): w.writerow([k]+[v[p] for p in P])
with open("formations.csv","w",newline="") as fh:
    w=csv.writer(fh); w.writerow(["id","name","family"]+P+["note"])
    for k,v in F.items():
        w.writerow([k,v["name"],v["family"]]+[v["over"].get(p,"") for p in P]+[v["note"]])
with open("formation_slots.csv","w",newline="") as fh:
    w=csv.writer(fh); w.writerow(["formation","slot","role","style","x","y"])
    for k,v in F.items():
        assert len(v["slots"])==10,(k,len(v["slots"]))
        for i,(r,s,x,y) in enumerate(v["slots"],1): w.writerow([k,i,r,s,x,y])
# style table (defined once, used by every formation): phase offsets (dx,dy) in pitch units, applied on top of base slot
STY={
"fullback":dict(BUILD=(0,8),ATTACK=(0,20),DEFEND=(3,-4),note="overlaps when team attacks; tucks in when defending"),
"wingback":dict(BUILD=(0,14),ATTACK=(0,28),DEFEND=(6,-10),note="very high in attack, drops to form back line"),
"stopper":dict(BUILD=(0,2),ATTACK=(0,8),DEFEND=(0,2),note="steps out to meet the striker"),
"ball_playing_cb":dict(BUILD=(0,4),ATTACK=(0,10),DEFEND=(0,-1),note="steps into midfield with the ball"),
"sweeper":dict(BUILD=(0,3),ATTACK=(0,8),DEFEND=(0,-4),note="stays behind the line, covers"),
"anchor":dict(BUILD=(0,-4),ATTACK=(0,4),DEFEND=(0,-2),note="holds in front of the defence"),
"deep_playmaker":dict(BUILD=(0,-2),ATTACK=(0,6),DEFEND=(0,-2),note="drops to collect, sits deep"),
"box_to_box":dict(BUILD=(0,2),ATTACK=(0,16),DEFEND=(0,-8),note="covers the full length"),
"playmaker":dict(BUILD=(0,0),ATTACK=(0,10),DEFEND=(0,-6),note="finds pockets between lines"),
"wide_mid":dict(BUILD=(0,2),ATTACK=(-2,14),DEFEND=(6,-8),note="tracks back to form the bank"),
"winger":dict(BUILD=(0,4),ATTACK=(-4,16),DEFEND=(5,-10),note="hugs the line, stretches play"),
"inside_forward":dict(BUILD=(0,2),ATTACK=(14,8),DEFEND=(10,-14),note="cuts inside toward goal"),
"shadow":dict(BUILD=(0,0),ATTACK=(0,12),DEFEND=(0,-8),note="runs beyond the striker"),
"target":dict(BUILD=(0,-2),ATTACK=(0,6),DEFEND=(0,-6),note="holds the ball up, wins aerials"),
"poacher":dict(BUILD=(0,2),ATTACK=(0,12),DEFEND=(0,-4),note="on the last defender's shoulder"),
}
with open("styles.csv","w",newline="") as fh:
    w=csv.writer(fh); w.writerow(["style","build_dx","build_dy","attack_dx","attack_dy","defend_dx","defend_dy","note"])
    for k,v in STY.items(): w.writerow([k,*v["BUILD"],*v["ATTACK"],*v["DEFEND"],v["note"]])
# preview
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig,axs=plt.subplots(2,5,figsize=(15,10))
col={"CB":"#5b8def","LB":"#5b8def","RB":"#5b8def","CDM":"#3fb68b","CM":"#3fb68b","CAM":"#e0b341","LW":"#e0b341","RW":"#e0b341","ST":"#e8604c"}
for ax,(k,v) in zip(axs.flat,F.items()):
    ax.set_facecolor("#2d6a3f"); ax.set_xlim(0,100); ax.set_ylim(0,100); ax.set_xticks([]); ax.set_yticks([])
    ax.plot([0,100],[50,50],c="white",lw=.6); ax.add_patch(plt.Circle((50,50),9,fill=False,ec="white",lw=.6))
    ax.scatter([50],[5],c="#ddd",s=90,edgecolors="k",zorder=3)
    for r,s,x,y in v["slots"]:
        ax.scatter([x],[y],c=col[r],s=110,edgecolors="k",zorder=3); ax.text(x,y-6,s,ha="center",fontsize=6,color="white")
    ax.set_title(f'{k}  {v["name"]}',fontsize=11)
plt.tight_layout(); plt.savefig("formations_preview.png",dpi=110)
print("ok")
