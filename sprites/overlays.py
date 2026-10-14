"""Upper-body overlays for SUPPORT cards: laid on top of whatever the player is already doing (running, dribbling, shooting...).
Only the named arm / head is touched; legs, torso and the other arm keep the base animation. apply(pose, overlay, side, w, f) -> new pose."""
import math

POSES = {                       # target arm values (s1, a1, s2, a2); s = pi/2 forward, bigger = raised
    'raise': (2.7, 0.2, 3.0, 0.1),
    'fist': (2.6, 0.25, 2.0, 0.25),
    'point': (1.55, 0.3, 1.55, 0.1),
}


def env(t, up=0.12, down=0.88):
    """0..1 weight for card progress t (0..1): quick ramp in, hold, ramp out"""
    if t <= 0 or t >= 1: return 0.0
    if t < up: return t / up
    if t > down: return (1 - t) / (1 - down)
    return 1.0


def apply(pose, overlay, side, w, f=0):
    if not overlay or w <= 0: return pose
    p = dict(pose)
    if overlay == 'scan':
        p['hyaw'] = pose.get('hyaw', 0.0) * (1 - w) + w * 0.85 * math.sin(f * 0.55)       # head sweeping while the body carries on
        p['hpitch'] = pose.get('hpitch', 0.0) * (1 - w) + w * -0.05
        return p
    tgt = POSES[overlay]
    for k, v in zip(('s1', 'a1', 's2', 'a2'), tgt):
        key = f'{side}_{k}'; p[key] = pose.get(key, 0.0) * (1 - w) + v * w
    if overlay == 'raise': p['hyaw'] = pose.get('hyaw', 0.0) * (1 - w) + w * 0.5 * math.sin(f * 0.5)    # glancing about while the arm goes up
    return p
