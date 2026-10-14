import csv, re
BLOCKS = {
'PASS': ('PS', '''Through Ball|1|68|18|10|Slips the ball between defenders into the runner's path.
Lofted Through|2|60|20|14|Floats the ball over the back line for a runner.
Driven Pass|1|78|12|8|Hard flat pass. Hard to intercept and harder to control.
One Two|2|66|18|14|Passes and darts into space for the instant return.
Backheel Pass|2|58|22|16|Surprise pass behind the standing foot.
No Look Pass|2|55|20|18|Disguises the target so defenders read it late.
Cross|1|64|16|10|Whips the ball into the box from wide.
Driven Cross|2|56|20|14|Low fast cross to the near post.
Cutback|2|62|18|14|Pulls the ball back from the byline to a runner.
Switch Play|1|72|12|12|Long diagonal to the far flank.
Rabona Cross|3|44|32|28|Crosses with the trailing leg. Hard to read.
Outside Foot Pass|1|70|15|10|Bends a pass round a defender with the outside of the boot.
Chipped Pass|2|62|18|14|Lifts the ball over a defender's reach.
Pass and Move|1|74|14|10|Plays the ball and starts a run in one move.
Killer Ball|3|46|28|26|A defence-splitting pass. Huge reward if it works.
Square Ball|1|86|6|6|Safe sideways pass that keeps possession.
Return Pass|1|80|8|8|Gives it straight back to the passer.
Long Ball Forward|1|60|16|12|Sends it long into the channel for the striker.
Corner Delivery|2|58|18|22|Whipped corner into the danger area.
Short Corner|1|76|10|14|Plays the corner short to a teammate.
Free Kick Cross|2|56|20|22|Floated free kick into the box.
Quick Free Kick|1|70|14|18|Takes it before the defence is set.
Lay Off|1|82|8|8|Cushions a pass back for a shooter.
Flick On|2|54|22|16|Glances it on with a header or heel.
Reverse Pass|3|48|28|26|Plays it the opposite way to the run.'''),
'DRIBBLE': ('DR', '''Step Over|1|74|14|10|Sells the defender the wrong way.
Drag Back|1|72|14|10|Pulls the ball back under the sole and turns.
Roulette|2|62|20|16|Spins round the ball past the defender.
Nutmeg|3|38|34|26|Passes the ball through the defender's legs.
Body Feint|1|78|10|8|Drops a shoulder to unbalance the marker.
Sombrero Flick|3|40|30|28|Flicks the ball over the head of the defender.
La Croqueta|2|66|18|14|Quick touch from foot to foot to slip past.
Elastico|2|60|22|18|Flicks the ball out then in. Leaves the defender behind.
Cruyff Turn|1|70|14|12|Drags the ball behind the standing leg and turns away.
Fake Shot Turn|2|68|16|14|Pretends to shoot then drives away.
Ball Roll|1|76|10|8|Rolls the ball sideways under the sole.
Shoulder Shield|1|70|14|10|Protects the ball with the body.
Hold Up Play|2|74|10|14|Receives with a back to goal and holds it.
Chop Cut|1|74|12|10|Cuts the ball across the body.
Stepover Chain|2|62|18|16|Two step overs and a burst.
Heel Flick|2|58|22|16|Back-heels the ball past the closing defender.
Drive Through|1|66|20|10|Powers straight through with the ball.
Skill Combo|2|60|20|20|Chains two moves for an exit that is hard to read.
Fake Pass|1|76|10|10|Dummies a pass to draw the defender out.
Quick Touch|1|82|8|6|Short controlled touch past pressure.
Spin Away|2|64|18|14|Turns on the spot away from the tackle.
Trap and Turn|1|78|10|8|Controls and spins in a single touch.
Slalom|3|48|26|24|Weaves between two defenders.
Burst of Pace|2|68|18|16|Accelerates past a defender at once.
Wall Run|2|62|20|16|Dribbles along the touchline.
Rainbow Flick|3|40|32|28|Flicks the ball over the defender from behind.
Outside Hook|1|72|14|10|Hooks the ball away from the tackle.
Pull Push|2|66|18|14|Drags it back then pushes it away.
Dummy Run|1|74|10|10|Lets the ball run through the legs to a teammate.
Showboat Spin|3|50|26|30|Spectacular spin that disrupts the defender.'''),
'SUPPORT': ('SP', '''Tiger Legs|2|90|5|24|For 3s your next dribble card gains success and a special move.
Leap Sprint|2|86|8|20|Bounds forward in a surge. Adds pace for 4s.
Muscle Up|2|90|5|24|For 3s your next challenge wins the shoulder charge.
Sharp Boots|1|88|4|18|For 3s your next shot card gains success.
Radar Vision|1|90|4|20|For 3s your next pass card gains success.
Calm Head|1|90|3|20|For 3s your next card ignores pressure.
Second Wind|2|88|5|30|Restores stamina to the selected player.
Hot Streak|3|80|10|40|After a success, your next card has a shorter cooldown.
Cooldown Pulse|3|85|8|45|Reduces the cooldown of your cards for 8s.
Reset Button|2|80|10|40|Instantly resets one card's cooldown.
Overdrive|3|78|12|50|Doubles the length of your buff windows.
Focus Chain|2|86|6|28|Extends your active buff by 2s.
Stamina Boost|1|90|3|22|Slows stamina drain for 10s.
Steady Hands|1|88|4|20|For 3s your next keeper or defend card gains success.
Chest Out|1|90|3|18|For 3s the player resists being knocked off the ball.
Cold Blood|2|84|8|30|A failed card adds no extra cooldown for 10s.
Rhythm|1|88|4|18|For 3s your next dribble and pass flow into each other.
Pace Surge|1|88|4|16|Raises top speed for 3s.
Wide Open|2|82|8|26|Draws a defender away from your runner.
Rally the Team|2|80|10|40|Boosts team morale for 15s.
Captain's Orders|3|84|8|45|Orders two teammates to hold a role for 10s.
Warm Up|1|92|2|20|The next card you play has a shorter cooldown.
Muscle Memory|2|86|6|28|A repeated card does not lose success.
Sixth Sense|2|82|8|30|Reveals the opponent's primed player.
Fresh Legs|2|88|5|36|Restores a tired player's pace.
Decoy Run|1|80|8|20|A teammate pulls defenders away.
Two Touch|1|90|3|16|For 3s your next pass or shot needs only two touches.
Battle Ready|2|86|6|26|For 3s your next tackle card gains success.
Ice Veins|2|80|10|34|For 3s your next penalty or free kick gains success.
Warp Boots|3|76|14|50|A short burst of pace at no stamina cost.'''),
'DEFEND': ('DF', '''Stand Tackle|1|90|8|8|Holds position and takes the ball cleanly.
Slide Tackle|2|94|97|14|Wins the ball but leaves you on the floor if it fails.
Poke Tackle|1|66|14|8|Pokes the ball away without committing.
Intercept Lane|1|70|12|10|Steps into the passing lane to cut it out.
Block Lane|1|72|10|10|Covers the shooting lane to block.
Tactical Foul|2|85|30|22|Stops the play with a foul. Risks a booking.
Recovery Sprint|1|76|10|14|Chases back at full pace.
Double Team|2|70|16|18|A second defender closes in. Winning odds rise.
Offside Trap|2|64|28|26|The line steps up together.
Jockey|1|82|8|8|Backs off and shadows the dribbler.
Press Trigger|2|72|16|16|Closes the ball carrier down at once.
Shirt Tug|1|68|24|14|Slows a runner. Risks a foul.
Shoulder Charge|2|66|18|14|Barges the carrier off the ball.
Clear the Lines|1|88|6|10|Hoofs it clear.
Last Ditch Block|2|60|20|18|Throws the body in front of the shot.
Header Clear|1|82|8|10|Heads a cross away.
Cut Out Cross|1|70|12|12|Moves to cut the cross off.
Snuff Out|2|72|16|16|Smothers the dribbler before the touch.
Shadow Marking|1|84|6|10|Sticks tight to a runner.
Zonal Cover|1|86|6|12|Covers a zone and picks up arrivals.
Drop Deep|1|90|4|12|Drops the line to stop a through ball.
Step Up|1|74|12|12|Pushes the line up as one.
Ball Hawk|2|66|18|18|Reads the next pass and leaps in.
Body Block|1|76|10|10|Shields the carrier from passing.
Wall Setup|1|86|6|20|Sets the free kick wall.
Wall Jump|1|62|14|10|The wall jumps at the shot.
Poacher's Guard|2|70|14|16|Tracks the nearest striker.
Rescue Tackle|2|70|20|20|A desperate stretch to win it back.
Sweep|3|56|28|26|Charges out of the line to clean up.
Clean Sheet Wall|3|64|14|36|The defence blocks everything for 6s.
Fox in the Box|2|74|12|18|Pins a striker in the box.
Backheel Clear|2|58|22|14|Flicks it clear off the line.
Trap the Winger|2|70|16|18|Forces the winger inside.
Tight Squeeze|2|68|18|18|Squeezes space for a dribbler.
Crunching Block|3|62|28|28|A heavy block that might hurt.'''),
'KEEPER': ('GK', '''Set Stance|1|90|3|8|Gets balanced and ready for the save.
Reach Dive|2|68|18|14|Stretches to the corner for a curler.
Smother|2|72|24|20|Rushes out to close the angle.
Punch Clear|1|78|12|12|Punches the cross away.
Claim Cross|2|70|20|16|Claims the cross high.
Sweeper Rush|3|60|30|26|Sprints out to clear the through ball.
Quick Throw|1|86|8|8|Throws it out to start an attack.
Big Hands|2|76|18|20|Holds the ball instead of parrying it.
Low Dive|1|72|12|10|Gets down fast to a low shot.
High Palm|2|66|20|16|Tips it over the bar.
Backpedal|1|64|18|12|Retreats to cover the chip.
Starfish|2|62|22|18|Spreads big in a one on one.
Parry Stance|1|74|12|12|Positions to parry rather than catch.
Penalty Guess|2|50|40|30|Commits to one corner at a penalty.
Wall Organiser|1|88|4|14|Sets the wall for the free kick.
Long Kick|1|70|12|10|Kicks long to the striker.
Roll Out|1|90|4|8|Rolls it short to a defender.
Throw Long|2|68|14|14|Hurls it to the winger.
Read the Run|2|70|14|18|Anticipates the through ball.
Cat Reflexes|3|58|20|32|A reflex save to a close shot.
Dominate Box|2|72|16|20|Takes charge of the box on a corner.
Near Post Guard|1|76|10|10|Covers the near post.
Far Post Reach|2|66|18|14|Moves to cover the far post.
Fingertip Save|3|56|24|28|Gets a fingertip to a curler.
Rebound Clear|1|80|8|10|Pushes the loose ball away from danger.'''),
'TITAN': ('TT', '''Zip Zap|6|88|10|60|Teleports past three defenders in a burst of lightning.
Gravity Cannon|6|82|22|60|The ball crushes under its own weight. Pace no keeper can hold.
Eagle's Eye|5|95|2|90|See every card the opponent holds for 10s.
Triple Weave|6|80|14|70|Dribbles past three defenders in slow motion.
Bicycle Kick|5|56|28|60|A spectacular overhead strike.
Time Stop|8|90|6|120|Freezes the pitch for 3s while you plan.
Rocket Legs|5|86|10|70|A massive sprint that outpaces everyone.
Iron Wall|6|84|8|80|Your defence becomes unbreakable for 6s.
Phantom Pass|5|78|16|70|A pass that cannot be intercepted.
Hundred Yard Strike|6|60|24|80|A shot from anywhere that swerves round everything.
Dragon Header|5|68|22|70|A header with power no keeper can stop.
Steel Goalkeeper|6|82|10|90|Your keeper saves anything for 6s.
Earthquake Tackle|5|76|20|70|A tackle that shakes the ground and floors nearby players.
Wind Walk|5|82|12|60|A dribble that cannot be tackled for 4s.
Meteor Shot|6|64|24|80|A shot that dips late and burns the keeper.
Chain Lightning|5|80|12|70|Passes jump between three teammates in an instant.
Black Hole|6|74|18|90|Pulls nearby defenders toward you.
Mirror Match|5|70|14|70|Copies the opponent's last card.
Second Heart|5|90|6|100|Restores all stamina to the team.
Titan Slide|5|78|24|70|A slide that cannot miss but leaves you stranded.
Skyfall|6|62|26|80|A lofted ball drops like a meteor from above.
Lock On|4|85|8|60|Your next shot cannot miss the target.
Dream Team|7|80|10|120|All teammates move in perfect sync for 8s.
Reality Bend|7|72|20|120|Rewinds your last play and tries again.
Chaos Control|6|70|22|90|Scrambles the opponent's cooldowns for 6s.'''),
}
rows = []
for r in csv.DictReader(open('shots.csv')):
    rows.append(dict(id=r['id'], name=r['name'], cat='SHOT', slots=r['slots'], succ=r['succ'], risk=r['risk'], cd=r['cd'], effect=r['effect']))
for cat, (pre, blk) in BLOCKS.items():
    for i, ln in enumerate(blk.strip().split('\n'), 1):
        n, sl, su, ri, cd, ds = ln.split('|')
        rows.append(dict(id=f'{pre}{i:02d}', name=n, cat=cat, slots=sl, succ=su, risk=ri, cd=cd, effect=ds))
for r in rows:
    r['kind'] = 'BUFF' if re.search(r'\bFor \d+s\b|\bfor \d+s\b', r['effect']) and r['cat'] in ('SUPPORT',) else 'ACTION'
    r['description'] = r.pop('effect')
keys = ['id', 'name', 'cat', 'slots', 'succ', 'risk', 'cd', 'kind', 'description']
with open('cards.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
from collections import Counter, defaultdict
c = Counter(r['cat'] for r in rows); print(len(rows), dict(c))
agg = defaultdict(list)
for r in rows: agg[r['cat']].append(r)
for k, v in agg.items():
    print(k, 'slots', min(int(x['slots']) for x in v), '-', max(int(x['slots']) for x in v), '| avg succ', round(sum(int(x['succ']) for x in v) / len(v)), '| avg risk', round(sum(int(x['risk']) for x in v) / len(v)), '| avg cd', round(sum(int(x['cd']) for x in v) / len(v)))
print('buffs', sum(1 for r in rows if r['kind'] == 'BUFF'))
ids = [r['id'] for r in rows]; assert len(ids) == len(set(ids))
names = [r['name'] for r in rows]; d = [n for n, k in Counter(names).items() if k > 1]; print('dup names', d)
