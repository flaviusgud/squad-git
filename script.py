import unreal
import os
import json
import re
from glob import glob

out = "D:/ws/sq5"
inst = "C:/avx/bin/SEPT/Squad/Content"

guns_types = ["GrenadeLaunchers", "MachineGuns", "Pistols", "Rifles", "RocketLaunchers", "SubmachineGuns"]
used_guns = set()
used_static = set()

def jd(x, p):
    pp = p.rsplit("/",1)[0]
    os.makedirs(f"{out}/{pp}", exist_ok=1)
    with open(f"{out}/{p}.json", "w") as f:
        json.dump(x, f, indent=2)

def strip(x):
    if isinstance(x, float) or isinstance(x, int):
        return x
    x = str(x)
    x = re.sub(" *\(0x.*\)", "", x)
    x = re.sub("<Struct 'Vector'", "", x)
    return re.sub("<Object ", "", x)

def itrarr(x, dep):
        if "Object" in str(x) or "Struct" in str(x):
            return itrdict(x, dep + 1)
        return strip(x)

def itrdict(x, dep):
    if dep > 3:
        return strip(x)[:128]
    d = {}
    for a in dir(x):
        try:
            aa = getattr(x, a)
            ts = str(type(aa))
            if "method" not in ts and a[0] != "_":
                if a.isupper():
                    continue
                if "Struct" in str(aa):
                    d[a] = itrdict(aa, dep + 1)
                elif "Array" in ts:
                    d[a] = [itrarr(bb, dep) for bb in aa]
                else:
                    aas = strip(aa)
                    if not isinstance(aas, str) or "Art" not in aas:
                        d[a] = aas
            aas = re.sub("' .*", "", strip(aa))[1:]
            if a == "equipable_item" and any([g in aas for g in guns_types]):
                used_guns.add(aas)
            if a == "item_static_info_class":
                used_static.add(aas)
            if a == "damage_falloff_curve":
                b = unreal.load_object(None, aas.split(".")[0])
                d[a] = [b.get_time_range(), b.get_value_range()[::-1]]
        except:
            pass
    return d

paths = ["Settings/Roles", "Settings/FactionSetups"]
for path in paths:
    for w in glob(f"{inst}/{path}/**/*.uasset", recursive = True):
        bp = w.split("\\", 1)[1].replace("\\", "/")[:-7]
        b = unreal.load_object(None, f"/Game/{path}/{bp}")
        jd(itrdict(b, 0), f"{path}/{bp}")
for gun in used_guns:
    b = unreal.load_object(None, gun)
    b = unreal.get_default_object(b)
    jd(itrdict(b, 0), gun.split(".")[0][5:])
for gun in used_static:
    b = unreal.load_object(None, gun)
    b = unreal.get_default_object(b)
    jd(itrdict(b, 0), gun.split(".")[0][5:])
paths = ["Blueprints/Items/Grenades", "Blueprints/Items/Projectiles"]
for path in paths:
    for w in glob(f"{inst}/{path}/**/BP_*.uasset", recursive = True):
        bp = w.split("\\", 1)[1].replace("\\", "/")[:-7]
        bpp = bp.rsplit("/", 1)
        b = unreal.load_object(None, f"/Game/{path}/{bp}.{bpp[-1]}_C")
        b = unreal.get_default_object(b)
        jd(itrdict(b, 0), f"{path}/{bp}")
