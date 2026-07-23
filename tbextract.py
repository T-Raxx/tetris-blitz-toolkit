"""Full game image extractor: every image across the 3 sources — DBPF `.db` banks, loose Cocos
sprite atlases (`*.plist`+`.png`), and standalone loose PNGs."""
import pathlib, shutil
import tbatlas, tbassets

def enumerate_sources(assets_dir=tbatlas.ASSETS):
    assets = pathlib.Path(assets_dir)
    out = []
    for db in tbatlas.list_db_banks(assets):
        out.append({"type": "db", "path": str(db)})
    cocos = assets / "Cocos2dxImages"
    plist_stems = set()
    for pl in sorted(cocos.rglob("*.plist")):
        out.append({"type": "atlas", "path": str(pl)})
        plist_stems.add((pl.parent, pl.stem))
    for png in sorted(cocos.rglob("*.png")):
        if (png.parent, png.stem) not in plist_stems:      # PNG without a same-stem atlas
            out.append({"type": "loose", "path": str(png)})
    return out

def extract_all(out_dir, assets_dir=tbatlas.ASSETS, include_db=True):
    out = pathlib.Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    by = {"db": 0, "atlas": 0, "loose": 0}; errors = []
    for s in enumerate_sources(assets_dir):
        t, p = s["type"], pathlib.Path(s["path"])
        try:
            if t == "db":
                if not include_db:
                    continue
                got = tbatlas.extract_db(str(p), str(out / "db" / p.stem))
                by["db"] += len(got)
            elif t == "atlas":
                atlas_png = p.with_suffix(".png")
                if not atlas_png.exists():
                    continue
                got = tbassets.extract_atlas(str(out / "atlas" / p.stem), plist=str(p), atlas=str(atlas_png))
                by["atlas"] += len(got)
            else:
                dst = out / "loose" / p.name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(p, dst); by["loose"] += 1
        except Exception as e:
            errors.append(f"{t}:{p.name}: {e}")
    return {"count": sum(by.values()), "by_type": by, "errors": errors, "out_dir": str(out)}
