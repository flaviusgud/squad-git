import json
import pandas as pd
from collections import defaultdict
from glob import glob


def jl(x):
    with open(x) as f:
        return json.load(f)


s2n = defaultdict(list)
paths = ["Rifles", "SubmachineGuns", "MachineGuns", "Pistols"]
for path in paths:
    for j in glob(f"Blueprints/Items/{path}/**/*.json", recursive=True):
        if "StaticInfo" in j:
            continue
        j = jl(j)
        wc = j["weapon_config"]
        if wc["max_mags"] == 1:
            continue
        d = {
            "rounds": wc["rounds_per_mag"],
            "reload": round(wc["tactical_reload_duration"], 1),
            "cost": int(j["ammo_per_rearm_item"]),
            "rpm": int(60 / wc["time_between_shots"]),
            "vel": int(wc["muzzle_velocity"] / 100),
            "AP(mm)": wc["armor_penetration_depth_millimeters"],
        }
        d["start_dmg"] = int(wc["damage_falloff_curve"][1][0])
        d["end_dmg"] = int(wc["damage_falloff_curve"][1][1])
        d["start_dist"] = int(wc["damage_falloff_curve"][0][0] / 100)
        d["end_dist"] = int(wc["damage_falloff_curve"][0][1] / 100)
        d["50dmg"] = -1
        if d["start_dmg"] > 50 and d["start_dmg"] < 100 and d["end_dmg"] < 50:
            off = (d["start_dmg"] - 50) / (d["start_dmg"] - d["end_dmg"])
            d["50dmg"] = int((d["start_dist"] + off * (d["end_dist"] - d["start_dist"])))
        s = j["item_static_info_class"].split(f"Items/")[1].split(".")[0]
        s = jl(f"Blueprints/Items/{s}.json")
        for st in ["stand", "crouch", "prone", "bipod"]:
            for ads in ["", "_ads"]:
                m = s[f"{st}{ads}_recoil_mean"]
                si = s[f"{st}{ads}_recoil_sigma"]
                for dim in "xyz":
                    d[f"{st}{ads}_{dim}"] = f"{m[dim]:.1f}±{si[dim]:.1f}"
        d["clamp"] = int(s["sway_data"]["limits"]["final_sway_clamp"])
        for st in ["standing", "crouch", "prone", "bipod"]:
            d[f"{st}_min"] = round(s["sway_data"]["stance_group"][st]["sway_min"], 1)

        s2n[json.dumps(d)].append(f"{j['display_name'].replace(' ', '')}>{wc['max_mags']}")

merged = []
for s, n in s2n.items():
    m = {"guns>mags": ", ".join(n)}
    m.update(json.loads(s))
    merged.append(m)
df = pd.DataFrame(merged)
df.to_excel("guns.xlsx", index=0)
